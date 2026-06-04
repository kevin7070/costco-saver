"""Receipt parser interface + structured output types.

Parsers turn a receipt image into a `StructuredReceipt` (plain dataclasses),
decoupled from persistence so the implementation can be swapped freely.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class StructuredLineItem:
    raw_name: str
    item_number: str | None = None
    quantity: int = 1
    unit_price: Decimal | None = None
    amount: Decimal | None = None
    item_type: str = "product"  # "product" | "service" | "discount"
    taxable: bool = False


@dataclass
class StructuredReceipt:
    store_location: str | None = None
    store_number: str | None = None
    purchase_date: str | None = None  # ISO "YYYY-MM-DD" if parseable
    receipt_number: str | None = None  # bottom barcode number (dedup / return ref)
    invoice_number: str | None = None
    line_items: list[StructuredLineItem] = field(default_factory=list)
    raw: dict = field(default_factory=dict)  # original model JSON, kept for review


class ReceiptParser(ABC):
    """Turns a receipt image into a StructuredReceipt."""

    @abstractmethod
    def parse(self, image_bytes: bytes, *, content_type: str = "image/jpeg") -> StructuredReceipt:
        ...
