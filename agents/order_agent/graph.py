"""The order agent's orchestration StateGraph.

Workflow:

    extract_intent
        -> (clarify)                       # confidence < 0.90
        -> confirm_with_customer
        -> check_inventory
            -> (failure)                   # stock unavailable
            -> process_payment
                -> arrange_shipping        # payment ok
                -> rollback_inventory      # payment failed -> failure
        -> save_order
        -> send_notification
        -> format_response
        -> END

The four side-effecting steps delegate to peer agents over A2A; ``save_order``
calls the order MCP directly. Every external dependency (LLM, peer A2A client,
order MCP client) is injected through :class:`OrderGraphDeps` so the graph can
be unit-tested with stubs and no network access.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from order_agent import config
from order_agent.intent import ExtractedOrderIntent
from order_agent.output_schemas import OrderConfirmation
from order_agent.prompts import EXTRACTION_SYSTEM_PROMPT, RESPONSE_SYSTEM_PROMPT
from order_agent.state import OrderState
from shared.correlation import format_correlation_token, new_correlation_id
from shared.guardrail_input import check_input_intent
from shared.guardrail_output import check_output, strip_sensitive
from shared.guardrail_reasoning import max_recursion_limit

logger = logging.getLogger("agentcart.order.graph")

# Signature of the injected peer caller: (peer_name, message_text) -> reply text
PeerCaller = Callable[[str, str], Awaitable[str]]
# Signature of the injected order-save callable: (kwargs) -> reply text
OrderSaver = Callable[..., Awaitable[str]]


@dataclass
class OrderGraphDeps:
    """External collaborators the graph depends on (injected for testing)."""

    llm: BaseChatModel
    call_peer: PeerCaller
    save_order: OrderSaver


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)
_TXN_PATTERN = re.compile(r"\b(txn[-_][A-Za-z0-9\-]+)", re.IGNORECASE)
_TRACK_PATTERN = re.compile(r"\b(trk[-_][A-Za-z0-9\-]+)", re.IGNORECASE)
_ORDER_PATTERN = re.compile(r"\b(ord[-_][A-Za-z0-9\-]+|ORD-[A-Za-z0-9\-]+)")


def _message_text(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        )
    return str(content)


def _parse_json_object(text: str) -> Optional[dict]:
    """Best-effort extraction of a JSON object from model output."""
    if not text:
        return None
    candidate = text.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK.search(candidate)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _looks_successful(text: str) -> bool:
    """Heuristic: did a peer/tool reply indicate success?"""
    if not text:
        return False
    lowered = text.lower()
    failure_markers = (
        "fail",
        "error",
        "declined",
        "insufficient",
        "unavailable",
        "not available",
        "out of stock",
        "rejected",
        "could not",
        "unable",
    )
    return not any(marker in lowered for marker in failure_markers)


def _first_match(pattern: re.Pattern[str], text: str) -> Optional[str]:
    if not text:
        return None
    match = pattern.search(text)
    return match.group(1) if match else None


# --------------------------------------------------------------------------- #
# Node implementations
# --------------------------------------------------------------------------- #


async def _extract_intent(state: OrderState, deps: OrderGraphDeps) -> dict:
    correlation_id = state.get("correlation_id") or new_correlation_id()
    message = state.get("customer_message", "")

    raw = await deps.llm.ainvoke(
        [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=message),
        ]
    )
    parsed = _parse_json_object(_message_text(raw)) or {}

    update: dict = {
        "correlation_id": correlation_id,
        "executed_steps": list(state.get("executed_steps", [])),
        "currency": config.DEFAULT_CURRENCY,
    }

    try:
        intent = ExtractedOrderIntent(**parsed)
    except Exception as exc:  # noqa: BLE001 - malformed extraction -> clarify
        logger.warning("intent extraction failed validation: %s", exc)
        update.update(
            intent=None,
            confidence_score=0.0,
            needs_clarification=True,
            status="pending_review",
            failure_reason="Could not understand the order request.",
        )
        return update

    guard = check_input_intent(
        intent,
        known_product_ids=config.known_product_ids(),
        known_customer_ids=config.known_customer_ids(),
    )

    customer = config.CUSTOMER_PROFILES.get(intent.customer_id)
    product = config.PRODUCT_CATALOG.get(intent.product_id)
    # Authoritative total from the catalog price, never the model's arithmetic.
    unit_price = product.unit_price if product else intent.unit_price
    total_amount = round(unit_price * intent.quantity, 2)

    update.update(
        intent=intent.model_dump(),
        confidence_score=intent.confidence_score,
        needs_clarification=guard.needs_clarification or not guard.passed,
        customer_name=customer.name if customer else intent.product_name,
        product_name=product.name if product else intent.product_name,
        quantity=intent.quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        address=intent.address,
        estimated_delivery=intent.delivery_date,
    )
    if not guard.passed:
        update["failure_reason"] = "; ".join(guard.reasons)
    return update


async def _clarify(state: OrderState, deps: OrderGraphDeps) -> dict:
    reason = state.get("failure_reason") or (
        "The order request was ambiguous; please confirm the product, "
        "quantity, and customer."
    )
    return {"status": "pending_review", "failure_reason": reason}


async def _confirm_with_customer(state: OrderState, deps: OrderGraphDeps) -> dict:
    # In this demo the confirmation is implicit (the workflow proceeds); the
    # node exists as the documented hook for a human-in-the-loop interrupt.
    return {}


async def _check_inventory(state: OrderState, deps: OrderGraphDeps) -> dict:
    intent = state.get("intent") or {}
    correlation_id = state["correlation_id"]
    steps = list(state.get("executed_steps", []))
    steps.append("check_inventory")

    message = (
        f"Reserve {intent.get('quantity')} unit(s) of product "
        f"{intent.get('product_id')}. First check stock, then reserve it. "
        f"{format_correlation_token(correlation_id)}"
    )
    reply = await deps.call_peer("inventory", message)
    ok = _looks_successful(reply)
    return {
        "inventory_result": reply,
        "inventory_ok": ok,
        "executed_steps": steps,
        **({} if ok else {
            "status": "failed",
            "failure_reason": f"Inventory unavailable: {reply}",
        }),
    }


async def _process_payment(state: OrderState, deps: OrderGraphDeps) -> dict:
    intent = state.get("intent") or {}
    correlation_id = state["correlation_id"]
    steps = list(state.get("executed_steps", []))
    steps.append("process_payment")

    message = (
        f"Charge customer {intent.get('customer_id')} amount "
        f"{state.get('total_amount')} currency {state.get('currency')} with "
        f"payment_method_token={config.DEMO_PAYMENT_TOKEN}. "
        f"{format_correlation_token(correlation_id)}"
    )
    reply = await deps.call_peer("payment", message)
    ok = _looks_successful(reply)
    transaction_id = _first_match(_TXN_PATTERN, reply)
    update: dict = {
        "payment_result": reply,
        "payment_ok": ok,
        "transaction_id": transaction_id,
        "executed_steps": steps,
    }
    if not ok:
        update["status"] = "failed"
        update["failure_reason"] = f"Payment declined: {reply}"
    return update


async def _arrange_shipping(state: OrderState, deps: OrderGraphDeps) -> dict:
    intent = state.get("intent") or {}
    address = state.get("address") or {}
    correlation_id = state["correlation_id"]
    steps = list(state.get("executed_steps", []))
    steps.append("arrange_shipping")

    message = (
        "Create a shipment for this order. Address: "
        f"line1={address.get('line1', '')}, city={address.get('city', '')}, "
        f"state={address.get('state', '')}, postcode={address.get('postcode', '')}, "
        f"country={address.get('country', 'AU')}. "
        f"Product {intent.get('product_id')}. "
        f"{format_correlation_token(correlation_id)}"
    )
    reply = await deps.call_peer("shipping", message)
    tracking_id = _first_match(_TRACK_PATTERN, reply)
    return {
        "shipping_result": reply,
        "tracking_id": tracking_id,
        "executed_steps": steps,
    }


async def _rollback_inventory(state: OrderState, deps: OrderGraphDeps) -> dict:
    intent = state.get("intent") or {}
    correlation_id = state["correlation_id"]
    steps = list(state.get("executed_steps", []))
    steps.append("rollback_inventory")

    message = (
        f"Release the reserved stock: {intent.get('quantity')} unit(s) of "
        f"product {intent.get('product_id')} back to inventory because payment "
        f"failed. {format_correlation_token(correlation_id)}"
    )
    reply = await deps.call_peer("inventory", message)
    return {
        "inventory_result": reply,
        "executed_steps": steps,
        "status": "failed",
        "failure_reason": state.get("failure_reason") or "Payment failed.",
    }


async def _save_order(state: OrderState, deps: OrderGraphDeps) -> dict:
    intent = state.get("intent") or {}
    correlation_id = state["correlation_id"]
    steps = list(state.get("executed_steps", []))
    steps.append("save_order")

    reply = await deps.save_order(
        customer_id=intent.get("customer_id"),
        product_id=intent.get("product_id"),
        quantity=state.get("quantity"),
        total_amount=state.get("total_amount"),
        currency=state.get("currency"),
        transaction_id=state.get("transaction_id"),
        tracking_id=state.get("tracking_id"),
        correlation_id=correlation_id,
    )
    order_id = _first_match(_ORDER_PATTERN, reply) or correlation_id
    return {
        "save_result": reply,
        "order_id": order_id,
        "executed_steps": steps,
    }


async def _send_notification(state: OrderState, deps: OrderGraphDeps) -> dict:
    intent = state.get("intent") or {}
    correlation_id = state["correlation_id"]
    steps = list(state.get("executed_steps", []))
    steps.append("send_notification")

    message = (
        f"Notify customer {intent.get('customer_id')} that order "
        f"{state.get('order_id')} for {state.get('quantity')} x "
        f"{state.get('product_name')} is confirmed. Channel email. "
        f"{format_correlation_token(correlation_id)}"
    )
    reply = await deps.call_peer("notification", message)
    return {"notification_result": reply, "executed_steps": steps}


def _deterministic_confirmation(state: OrderState) -> OrderConfirmation:
    """Build an OrderConfirmation purely from workflow state (the fallback)."""
    status = state.get("status")
    if status not in ("confirmed", "failed", "pending_review"):
        status = "confirmed" if state.get("payment_ok") else "failed"
    return OrderConfirmation(
        order_id=state.get("order_id") or state.get("correlation_id", "unknown"),
        status=status,
        customer_name=state.get("customer_name", "unknown"),
        product_name=state.get("product_name", "unknown"),
        quantity=int(state.get("quantity", 1) or 1),
        unit_price=float(state.get("unit_price", 0.0) or 0.0),
        total_amount=float(state.get("total_amount", 0.0) or 0.0),
        currency=state.get("currency", config.DEFAULT_CURRENCY),
        transaction_id=state.get("transaction_id"),
        tracking_id=state.get("tracking_id"),
        estimated_delivery=state.get("estimated_delivery"),
        failure_reason=state.get("failure_reason"),
        correlation_id=state.get("correlation_id", "unknown"),
    )


async def _format_response(state: OrderState, deps: OrderGraphDeps) -> dict:
    """Parse the LLM's confirmation, retry once, then fall back deterministically."""
    facts = {
        "order_id": state.get("order_id") or state.get("correlation_id"),
        "status": state.get("status")
        or ("confirmed" if state.get("payment_ok") else "failed"),
        "customer_name": state.get("customer_name"),
        "product_name": state.get("product_name"),
        "quantity": state.get("quantity"),
        "unit_price": state.get("unit_price"),
        "total_amount": state.get("total_amount"),
        "currency": state.get("currency"),
        "transaction_id": state.get("transaction_id"),
        "tracking_id": state.get("tracking_id"),
        "estimated_delivery": state.get("estimated_delivery"),
        "failure_reason": state.get("failure_reason"),
        "correlation_id": state.get("correlation_id"),
    }
    prompt = (
        "Workflow outcome (use these values verbatim):\n"
        + json.dumps(facts, default=str)
    )

    confirmation: Optional[OrderConfirmation] = None
    for attempt in range(2):
        try:
            raw = await deps.llm.ainvoke(
                [
                    SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
            )
            parsed = _parse_json_object(_message_text(raw))
            if parsed is not None:
                confirmation = OrderConfirmation(**parsed)
                break
        except Exception as exc:  # noqa: BLE001 - retry then fall back
            logger.warning("format_response attempt %d failed: %s", attempt, exc)

    if confirmation is None:
        confirmation = _deterministic_confirmation(state)

    # Guardrail 5: the LLM may phrase the response, but it never decides the
    # money, the outcome, or the identifiers. Those come from workflow state.
    authoritative = _deterministic_confirmation(state)
    confirmation.status = authoritative.status
    confirmation.failure_reason = authoritative.failure_reason
    confirmation.order_id = authoritative.order_id
    confirmation.transaction_id = authoritative.transaction_id
    confirmation.tracking_id = authoritative.tracking_id
    confirmation.total_amount = authoritative.total_amount
    confirmation.unit_price = authoritative.unit_price
    confirmation.quantity = authoritative.quantity
    confirmation.currency = authoritative.currency
    confirmation.correlation_id = authoritative.correlation_id

    payload = strip_sensitive(confirmation.model_dump())
    amount_charged = (
        state.get("total_amount") if state.get("payment_ok") else None
    )
    output_check = check_output(payload, amount_charged=amount_charged)
    if not output_check.passed:
        logger.warning("output guardrail flagged: %s", output_check.reasons)
        # Rebuild deterministically to guarantee a consistent payload.
        payload = strip_sensitive(_deterministic_confirmation(state).model_dump())

    return {"confirmation": payload, "status": payload["status"]}


# --------------------------------------------------------------------------- #
# Conditional edges
# --------------------------------------------------------------------------- #


def _after_extract(state: OrderState) -> str:
    if state.get("needs_clarification") or state.get("intent") is None:
        return "clarify"
    return "confirm_with_customer"


def _after_inventory(state: OrderState) -> str:
    return "process_payment" if state.get("inventory_ok") else "format_response"


def _after_payment(state: OrderState) -> str:
    return "arrange_shipping" if state.get("payment_ok") else "rollback_inventory"


# --------------------------------------------------------------------------- #
# Graph construction
# --------------------------------------------------------------------------- #


def build_order_graph(deps: OrderGraphDeps):
    """Compile the order workflow StateGraph with the supplied dependencies."""

    def _bind(fn):
        async def _node(state: OrderState) -> dict:
            return await fn(state, deps)

        _node.__name__ = fn.__name__
        return _node

    graph = StateGraph(OrderState)

    graph.add_node("extract_intent", _bind(_extract_intent))
    graph.add_node("clarify", _bind(_clarify))
    graph.add_node("confirm_with_customer", _bind(_confirm_with_customer))
    graph.add_node("check_inventory", _bind(_check_inventory))
    graph.add_node("process_payment", _bind(_process_payment))
    graph.add_node("arrange_shipping", _bind(_arrange_shipping))
    graph.add_node("rollback_inventory", _bind(_rollback_inventory))
    graph.add_node("save_order", _bind(_save_order))
    graph.add_node("send_notification", _bind(_send_notification))
    graph.add_node("format_response", _bind(_format_response))

    graph.add_edge(START, "extract_intent")
    graph.add_conditional_edges(
        "extract_intent",
        _after_extract,
        {"clarify": "clarify", "confirm_with_customer": "confirm_with_customer"},
    )
    graph.add_edge("clarify", "format_response")
    graph.add_edge("confirm_with_customer", "check_inventory")
    graph.add_conditional_edges(
        "check_inventory",
        _after_inventory,
        {"process_payment": "process_payment", "format_response": "format_response"},
    )
    graph.add_conditional_edges(
        "process_payment",
        _after_payment,
        {
            "arrange_shipping": "arrange_shipping",
            "rollback_inventory": "rollback_inventory",
        },
    )
    graph.add_edge("arrange_shipping", "save_order")
    graph.add_edge("rollback_inventory", "format_response")
    graph.add_edge("save_order", "send_notification")
    graph.add_edge("send_notification", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()


def initial_state(customer_message: str) -> OrderState:
    """Seed the workflow state with a fresh correlation id."""
    return {
        "customer_message": customer_message,
        "correlation_id": new_correlation_id(),
        "executed_steps": [],
        "currency": config.DEFAULT_CURRENCY,
    }


def recursion_config() -> dict:
    """Runtime config applying the configured recursion limit."""
    return {"recursion_limit": max_recursion_limit()}
