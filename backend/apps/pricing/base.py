"""Price provider interface + structured result type.

Providers turn an item number (or search query) into a `PriceResult` (plain
dataclass), decoupled from persistence so the implementation can be swapped
freely. The default provider is a no-op; a real provider is injected at runtime
via `settings.PRICE_PROVIDER` (dotted path) and lives outside this repo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class PriceResult:
    item_number: str
    name: str | None = None
    url: str | None = None
    current_price: Decimal | None = None
    on_sale: bool = False
    currency: str = "CAD"
    source: str = "provider"
    raw: dict = field(default_factory=dict)  # original provider payload


class PriceProvider(ABC):
    """Looks up the current price of a product by item number or search query."""

    @abstractmethod
    def lookup(self, item_number: str) -> PriceResult | None:
        ...

    @abstractmethod
    def search(self, query: str) -> list[PriceResult]:
        ...
