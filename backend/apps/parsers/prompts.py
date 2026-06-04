"""Prompt for receipt → structured JSON extraction."""

RECEIPT_EXTRACTION_PROMPT = """You are a Costco receipt parser. Read the receipt image and extract it as JSON.

Return ONLY a JSON object (no prose, no markdown fences) with this exact shape:
{
  "store_location": string | null,
  "purchase_date": "YYYY-MM-DD" | null,
  "line_items": [
    {
      "raw_name": string,            // item name exactly as printed
      "item_number": string | null,  // Costco item number if printed
      "quantity": integer,
      "unit_price": number | null,
      "amount": number | null,        // line total
      "item_type": "product" | "service"
    }
  ]
}

Rules:
- "item_type" is "service" for non-merchandise lines (membership, Costco Travel,
  insurance, tire/auto install service, optical, pharmacy, gas, food court);
  everything else is "product".
- Do NOT include tax, subtotal, total, or payment lines in line_items.
- Use null when a value is not present. Numbers must be plain (no "$", no commas).
"""
