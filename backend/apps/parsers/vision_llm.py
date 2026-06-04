"""Vision-LLM receipt parser — calls a self-hosted OpenAI-compatible endpoint.

Endpoint / model / key all come from env (RECEIPT_LLM_*); nothing is hardcoded.
PDF receipts are rendered to PNG (page 1) before sending. OCR is imperfect, so
the result is always subject to user review before it is trusted.
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

_VALID_TYPES = {"product", "service", "discount"}


class VisionLLMParser(ReceiptParser):
    def __init__(self) -> None:
        self._client = OpenAI(
            base_url=settings.RECEIPT_LLM_BASE_URL,
            api_key=settings.RECEIPT_LLM_API_KEY or "noop",
            timeout=settings.RECEIPT_LLM_TIMEOUT,
        )
        self._model = settings.RECEIPT_LLM_MODEL

    def parse(self, file_bytes: bytes, *, content_type: str = "image/jpeg") -> StructuredReceipt:
        png, mime = self._ensure_image(file_bytes, content_type)
        data_uri = f"data:{mime};base64," + base64.b64encode(png).decode()
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": RECEIPT_EXTRACTION_PROMPT},
                {"type": "image_url", "image_url": {"url": data_uri}},
            ]}],
            max_tokens=2048,
            temperature=0,
            # This model ships a "thinking" mode that spends tokens on
            # reasoning_content; disable it so JSON comes back in `content`.
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        content = (resp.choices[0].message.content or "").strip()
        return self._to_structured(self._extract_json(content))

    @staticmethod
    def _ensure_image(file_bytes: bytes, content_type: str) -> tuple[bytes, str]:
        """Render a PDF (page 1) to PNG; pass images through unchanged."""
        is_pdf = content_type == "application/pdf" or file_bytes[:5] == b"%PDF-"
        if not is_pdf:
            return file_bytes, content_type
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            pix = doc.load_page(0).get_pixmap(dpi=200)
            return pix.tobytes("png"), "image/png"
        finally:
            doc.close()

    @staticmethod
    def _extract_json(content: str) -> dict:
        # Tolerate stray prose / code fences around the JSON object.
        start, end = content.find("{"), content.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError(f"no JSON object in model output: {content[:200]!r}")
        return json.loads(content[start : end + 1])

    @classmethod
    def _to_structured(cls, data: dict) -> StructuredReceipt:
        items = []
        for raw in data.get("line_items", []):
            it = raw.get("item_type")
            items.append(StructuredLineItem(
                raw_name=str(raw.get("raw_name", "")).strip(),
                item_number=cls._str(raw.get("item_number")),
                quantity=int(raw.get("quantity") or 1),
                unit_price=cls._dec(raw.get("unit_price")),
                amount=cls._dec(raw.get("amount")),
                item_type=it if it in _VALID_TYPES else "product",
                taxable=bool(raw.get("taxable")),
            ))
        return StructuredReceipt(
            store_location=cls._str(data.get("store_location")),
            store_number=cls._str(data.get("store_number")),
            purchase_date=cls._str(data.get("purchase_date")),
            receipt_number=cls._str(data.get("receipt_number")),
            invoice_number=cls._str(data.get("invoice_number")),
            line_items=items,
            raw=data,
        )

    @staticmethod
    def _str(v) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @staticmethod
    def _dec(value) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
