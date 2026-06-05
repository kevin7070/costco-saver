"""Default no-op price provider.

Ships in this repo so a fresh clone is inert: no external calls, no data source.
A real provider is injected at runtime via `settings.PRICE_PROVIDER`.
"""

from __future__ import annotations

from .base import PriceProvider, PriceResult


class NullProvider(PriceProvider):
    """Returns nothing. The default when no provider is configured."""

    def lookup(self, item_number: str) -> PriceResult | None:
        return None

    def search(self, query: str) -> list[PriceResult]:
        return []
