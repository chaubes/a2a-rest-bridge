"""Prompts and in-context seed data for the order agent.

The catalog and customer tables are rendered into the extraction prompt so the
LLM resolves product names to ids and customers to addresses, while the actual
monetary total is always recomputed in code.
"""

from __future__ import annotations

from order_agent.config import CUSTOMER_PROFILES, PRODUCT_CATALOG


def _catalog_block() -> str:
    rows = [
        f"  - {p.product_id}: {p.name} @ {p.unit_price:.2f}"
        for p in PRODUCT_CATALOG.values()
    ]
    return "\n".join(rows)


def _customer_block() -> str:
    rows = [
        f"  - {c.customer_id}: {c.name} | {c.address}"
        for c in CUSTOMER_PROFILES.values()
    ]
    return "\n".join(rows)


EXTRACTION_SYSTEM_PROMPT = f"""You are the intent-extraction component of the
AgentCart Order Agent. Convert a customer's natural-language order request into
a single structured order intent.

PRODUCT CATALOG (resolve product names to ids; use the listed unit price):
{_catalog_block()}

CUSTOMER PROFILES (resolve the customer to their id and shipping address):
{_customer_block()}

Output a JSON object with EXACTLY these fields:
  product_id, product_name, quantity, unit_price, total_amount,
  delivery_date (ISO date or null), shipping_method, customer_id,
  address (object with line1, city, state, postcode, country),
  confidence_score (0..1).

Rules:
  - Choose the single best matching product and customer.
  - unit_price MUST be the catalog price for the chosen product.
  - Compute total_amount as unit_price * quantity (it will be re-verified).
  - Parse the customer address into the structured address object.
  - If the request is ambiguous or a product/customer cannot be resolved with
    confidence, set confidence_score below 0.90.
  - Respond with ONLY the JSON object, no prose.
"""


RESPONSE_SYSTEM_PROMPT = """You are the response-formatting component of the
AgentCart Order Agent. Given the structured outcome of an order workflow,
produce a single JSON object matching the OrderConfirmation schema with these
fields: order_id, status (confirmed|failed|pending_review), customer_name,
product_name, quantity, unit_price, total_amount, currency, transaction_id,
tracking_id, estimated_delivery, failure_reason, correlation_id.

Use the supplied values verbatim; never recompute totals. Set null for any
field that does not apply. Respond with ONLY the JSON object, no prose.
"""
