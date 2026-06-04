"""Tests for the vision-LLM receipt parser (endpoint mocked)."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.parsers import StructuredReceipt
from apps.parsers.vision_llm import VisionLLMParser


def _fake_completion(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.fixture
def parser(settings):
    settings.RECEIPT_LLM_BASE_URL = "http://test/v1"
    settings.RECEIPT_LLM_MODEL = "test-model"
    settings.RECEIPT_LLM_API_KEY = "test"
    settings.RECEIPT_LLM_TIMEOUT = 30
    return VisionLLMParser()


def test_parse_extracts_line_items(parser):
    content = """{
      "store_location": "Costco Scarborough",
      "purchase_date": "2026-05-01",
      "line_items": [
        {"raw_name": "KS WATER 40PK", "item_number": "1234567", "quantity": 1, "unit_price": 4.99, "amount": 4.99, "item_type": "product"},
        {"raw_name": "MEMBERSHIP", "item_number": null, "quantity": 1, "unit_price": 60, "amount": 60, "item_type": "service"}
      ]
    }"""
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion(content)):
        result = parser.parse(b"fakeimagebytes")
    assert isinstance(result, StructuredReceipt)
    assert result.store_location == "Costco Scarborough"
    assert result.purchase_date == "2026-05-01"
    assert len(result.line_items) == 2
    assert result.line_items[0].item_number == "1234567"
    assert result.line_items[0].unit_price == Decimal("4.99")
    assert result.line_items[1].item_type == "service"


def test_parse_tolerates_prose_and_fences(parser):
    content = 'Here is the result:\n```json\n{"line_items": []}\n```\nDone.'
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion(content)):
        result = parser.parse(b"x")
    assert result.line_items == []


def test_parse_raises_when_no_json(parser):
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion("no json here")):
        with pytest.raises(ValueError):
            parser.parse(b"x")


def test_unparseable_price_becomes_none(parser):
    content = '{"line_items": [{"raw_name": "ODD", "unit_price": "N/A", "amount": null}]}'
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion(content)):
        result = parser.parse(b"x")
    assert result.line_items[0].unit_price is None
    assert result.line_items[0].item_type == "product"
