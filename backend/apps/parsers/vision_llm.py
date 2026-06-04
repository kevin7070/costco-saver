"""Vision-LLM receipt parser — calls a self-hosted OpenAI-compatible endpoint.

Endpoint / model / key all come from env (RECEIPT_LLM_*); nothing is hardcoded.
"""

from __future__ import annotations

import base64
import json
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from openai import OpenAI

from .base import ReceiptParser, StructuredLineItem, StructuredReceipt
from .prompts import RECEIPT_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class VisionLLMParser(ReceiptParser):
    def __init__(self) -> None:
        self._client = OpenAI(
            base_url=settings.RECEIPT_LLM_BASE_URL,
            api_key=settings.RECEIPT_LLM_API_KEY or "noop",
            timeout=settings.RECEIPT_LLM_TIMEOUT,
        )
        self._model = settings.RECEIPT_LLM_MODEL

    def parse(self, image_bytes: bytes, *, content_type: str = "image/jpeg") -> StructuredReceipt:
        data_uri = f"data:{content_type};base64," + base64.b64encode(image_bytes).decode()
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": RECEIPT_EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            max_tokens=2048,
            temperature=0,
            # This model ships a "thinking" mode that spends tokens on
            # `reasoning_content`; disable it so JSON comes back in `content`.
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        content = (resp.choices[0].message.content or "").strip()
        return self._to_structured(self._extract_json(content))

    @staticmethod
    def _extract_json(content: str) -> dict:
        # Tolerate stray prose / code fences around the JSON object.
        start, end = content.find("{"), content.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError(f"no JSON object in model output: {content[:200]!r}")
        return json.loads(content[start : end + 1])

    @classmethod
    def _to_structured(cls, data: dict) -> StructuredReceipt:
        items = [
            StructuredLineItem(
                raw_name=str(raw.get("raw_name", "")).strip(),
                item_number=str(raw["item_number"]).strip() if raw.get("item_number") else None,
                quantity=int(raw.get("quantity") or 1),
                unit_price=cls._dec(raw.get("unit_price")),
                amount=cls._dec(raw.get("amount")),
                item_type="service" if raw.get("item_type") == "service" else "product",
            )
            for raw in data.get("line_items", [])
        ]
        return StructuredReceipt(
            store_location=data.get("store_location") or None,
            purchase_date=data.get("purchase_date") or None,
            line_items=items,
            raw=data,
        )

    @staticmethod
    def _dec(value) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
