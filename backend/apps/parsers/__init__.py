"""Pluggable receipt parsers."""

from .base import ReceiptParser, StructuredLineItem, StructuredReceipt

__all__ = ["ReceiptParser", "StructuredLineItem", "StructuredReceipt", "get_parser"]


def get_parser() -> ReceiptParser:
    """Return the configured receipt parser (currently the vision-LLM one)."""
    from .vision_llm import VisionLLMParser

    return VisionLLMParser()
