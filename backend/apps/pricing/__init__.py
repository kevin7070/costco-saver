"""Pluggable price providers.

The concrete provider is resolved at runtime from `settings.PRICE_PROVIDER`
(a dotted path), defaulting to the no-op `NullProvider`. This indirection keeps
the real provider implementation out of this repo entirely.
"""

from .base import PriceProvider, PriceResult

__all__ = ["PriceProvider", "PriceResult", "get_price_provider"]

_DEFAULT_PROVIDER = "apps.pricing.null_provider.NullProvider"


def get_price_provider() -> PriceProvider:
    """Return the configured price provider (default: NullProvider)."""
    from django.conf import settings
    from django.utils.module_loading import import_string

    dotted = getattr(settings, "PRICE_PROVIDER", _DEFAULT_PROVIDER) or _DEFAULT_PROVIDER
    return import_string(dotted)()
