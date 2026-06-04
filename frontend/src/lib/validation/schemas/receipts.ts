import { z } from "zod";

export const lineItemReviewSchema = z.object({
  raw_name: z.string().min(1, "Name is required"),
  item_number: z.string().optional().default(""),
  quantity: z.coerce.number().int().min(1).default(1),
  // prices kept as strings to preserve decimals; backend parses to Decimal
  unit_price: z.string().optional().default(""),
  amount: z.string().optional().default(""),
  item_type: z.enum(["product", "service", "discount"]),
  taxable: z.boolean().default(false),
});

export const receiptReviewSchema = z.object({
  store_location: z.string().optional().default(""),
  store_number: z.string().optional().default(""),
  purchase_date: z.string().optional().default(""), // YYYY-MM-DD
  receipt_number: z.string().optional().default(""),
  invoice_number: z.string().optional().default(""),
  line_items: z.array(lineItemReviewSchema),
});

export type LineItemReviewForm = z.infer<typeof lineItemReviewSchema>;
export type ReceiptReviewForm = z.infer<typeof receiptReviewSchema>;
