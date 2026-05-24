"""Configuration and seed data for the order agent.

Holds the in-context PRODUCT CATALOG and CUSTOMER PROFILES used to resolve
product names to ids and customers to addresses, plus the peer-agent and MCP
URLs read from the environment. Monetary totals are always derived from the
catalog ``unit_price`` in code, never from the model's arithmetic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

AGENT_NAME = "order-agent"
PORT = 10010
HOST = "0.0.0.0"

DEFAULT_CURRENCY = "AUD"
# A placeholder payment instrument; real tokens would arrive from a PSP. This
# is intentionally a non-secret demo value, never a real card credential.
DEMO_PAYMENT_TOKEN = "tok_demo_visa"


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    unit_price: float


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    address: str


PRODUCT_CATALOG: dict[str, Product] = {
    "WB-001": Product("WB-001", "Blue Widget", 14.99),
    "WB-002": Product("WB-002", "Red Widget", 12.99),
    "WR-001": Product("WR-001", "Widget Rack", 49.99),
    "WH-001": Product("WH-001", "Widget Holder", 7.99),
    "WS-001": Product("WS-001", "Widget Set (Assorted)", 39.99),
}

CUSTOMER_PROFILES: dict[str, Customer] = {
    "C-001": Customer(
        "C-001", "Alice Johnson", "Level 12, 100 George St, Sydney NSW 2000, AU"
    ),
    "C-002": Customer(
        "C-002", "Bob Smith", "42 Queen St, Melbourne VIC 3000, AU"
    ),
    "C-003": Customer(
        "C-003", "Carol Davis", "15 Eagle St, Brisbane QLD 4000, AU"
    ),
}


def known_product_ids() -> set[str]:
    return set(PRODUCT_CATALOG)


def known_customer_ids() -> set[str]:
    return set(CUSTOMER_PROFILES)


def unit_price_for(product_id: str) -> float | None:
    product = PRODUCT_CATALOG.get(product_id)
    return product.unit_price if product else None


def public_url() -> str:
    """Base URL the order agent advertises in its AgentCard."""
    return os.getenv("ORDER_AGENT_URL", f"http://localhost:{PORT}")


def peer_urls() -> dict[str, str]:
    """A2A base URLs of the four peer agents."""
    return {
        "inventory": os.getenv(
            "INVENTORY_AGENT_URL", "http://localhost:10011"
        ),
        "payment": os.getenv("PAYMENT_AGENT_URL", "http://localhost:10012"),
        "shipping": os.getenv("SHIPPING_AGENT_URL", "http://localhost:10013"),
        "notification": os.getenv(
            "NOTIFICATION_AGENT_URL", "http://localhost:10014"
        ),
    }


def order_mcp_servers() -> dict[str, str]:
    """The order MCP server the order agent calls directly for save_order."""
    return {"order": os.getenv("ORDER_MCP_URL", "http://localhost:9004")}
