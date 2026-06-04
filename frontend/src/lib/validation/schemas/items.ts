import { z } from "zod";

import { optionalString, requiredString } from "../refinements";

export const itemCreateSchema = z.object({
  name: requiredString("Item name"),
  description: optionalString,
});

export type ItemCreateForm = z.infer<typeof itemCreateSchema>;

export const itemUpdateSchema = itemCreateSchema.partial();
export type ItemUpdateForm = z.infer<typeof itemUpdateSchema>;
