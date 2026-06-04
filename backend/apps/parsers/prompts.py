"""Prompt for receipt → structured JSON extraction.

Tuned against a real Costco receipt (2026-06-04): giving an alphanumeric
item_number example matters (the model only reads letters when shown one),
and the discount / raw_name / store / taxable rules below were each needed to
fix a concrete failure. OCR is still imperfect → user review is mandatory.
"""

RECEIPT_EXTRACTION_PROMPT = """You are a Costco receipt parser. Read the receipt image and extract ONLY a JSON object (no prose, no markdown fences):
{
  "store_location": string | null,   // warehouse name from the TOP, e.g. "Markham #151"
  "store_number": string | null,     // warehouse number, e.g. "151"
  "purchase_date": "YYYY-MM-DD" | null,
  "receipt_number": string | null,   // the long barcode number at the BOTTOM of the receipt
  "invoice_number": string | null,
  "line_items": [
    {
      "raw_name": string,            // product NAME only
      "item_number": string | null,  // code at the start of the line
      "quantity": integer,
      "unit_price": number | null,
      "amount": number | null,        // line total
      "item_type": "product" | "service" | "discount",
      "taxable": boolean
    }
  ]
}

Rules:
- "item_number" = the code at the start of the line, copied EXACTLY as printed. It MAY contain letters, e.g. "207SE40" or "8523320Z" — do not turn letters into digits.
- A line whose amount has a TRAILING MINUS (e.g. "6.00-") is an instant-savings DISCOUNT applied to the item above it, NOT a product. Output it with "item_type":"discount" and a NEGATIVE amount.
- "raw_name" = the product NAME only. Do NOT repeat the item number inside raw_name.
- "taxable" = true if the line is flagged (e.g. a trailing "H" for HST), else false.
- "item_type":"service" for non-merchandise (membership, travel, insurance, optical, pharmacy, gas, food court).
- "store_location" = the warehouse at the TOP of the receipt; ignore the "Whse:" line at the bottom.
- Do NOT include tax / subtotal / total / payment lines in line_items.
- Use null when a value is not present. Numbers must be plain (no "$", no commas).
"""
