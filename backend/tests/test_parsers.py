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


def test_parse_full_receipt(parser):
    content = """{
      "store_location": "Markham #151", "store_number": "151",
      "purchase_date": "2026-06-04",
      "receipt_number": "22015120500102606040916", "invoice_number": "205663",
      "line_items": [
        {"raw_name": "X-LIGHT OIL", "item_number": "142372", "quantity": 1, "unit_price": 28.99, "amount": 28.99, "item_type": "product", "taxable": false},
        {"raw_name": "INSTANT SAVINGS", "item_number": "207SE40", "quantity": 1, "unit_price": -6.0, "amount": -6.0, "item_type": "discount", "taxable": false},
        {"raw_name": "NEOFLAM 12PC", "item_number": "8523320Z", "quantity": 1, "unit_price": 29.99, "amount": 29.99, "item_type": "product", "taxable": true},
        {"raw_name": "MEMBERSHIP", "item_number": null, "quantity": 1, "unit_price": 60, "amount": 60, "item_type": "service", "taxable": false}
      ]
    }"""
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion(content)):
        r = parser.parse(b"\xff\xd8fakejpeg")
    assert isinstance(r, StructuredReceipt)
    assert r.store_location == "Markham #151"
    assert r.store_number == "151"
    assert r.receipt_number == "22015120500102606040916"
    assert r.invoice_number == "205663"
    assert len(r.line_items) == 4
    # alphanumeric item_number preserved
    assert r.line_items[1].item_number == "207SE40"
    # discount: negative amount + item_type
    assert r.line_items[1].item_type == "discount"
    assert r.line_items[1].amount == Decimal("-6.0")
    # taxable flag carried through
    assert r.line_items[2].taxable is True
    assert r.line_items[3].item_type == "service"


def test_parse_tolerates_prose_and_fences(parser):
    content = 'Here is the result:\n```json\n{"line_items": []}\n```\nDone.'
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion(content)):
        assert parser.parse(b"x").line_items == []


def test_parse_raises_when_no_json(parser):
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion("no json here")):
        with pytest.raises(ValueError):
            parser.parse(b"x")


def test_unparseable_price_becomes_none(parser):
    content = '{"line_items": [{"raw_name": "ODD", "unit_price": "N/A", "amount": null, "item_type": "product"}]}'
    with patch.object(parser._client.chat.completions, "create", return_value=_fake_completion(content)):
        li = parser.parse(b"x").line_items[0]
    assert li.unit_price is None
    assert li.item_type == "product"
