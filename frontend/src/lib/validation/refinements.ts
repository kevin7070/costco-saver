/**
 * Shared Zod schemas + refinements — reuse across all forms.
 */

import { z } from "zod";

import { patterns } from "./patterns";

export const emailSchema = z
  .string()
  .min(1, "Email is required")
  .regex(patterns.email, "Invalid email format");

export const optionalEmailSchema = z
  .string()
  .optional()
  .refine((v) => !v || patterns.email.test(v), "Invalid email format");

export const optionalPhoneSchema = z
  .string()
  .optional()
  .refine(
    (v) => !v || v.replace(/\D/g, "").length >= 10,
    "Phone number too short",
  );

export const normalizedUrlSchema = z
  .string()
  .transform((v) => (v.match(/^https?:\/\//) ? v : `https://${v}`))
  .pipe(z.string().url("Invalid URL"));

export const optionalUrlSchema = z
  .string()
  .optional()
  .transform((v) => (!v ? undefined : v.match(/^https?:\/\//) ? v : `https://${v}`))
  .pipe(z.string().url("Invalid URL").optional());

export const requiredString = (label: string) =>
  z.string().min(1, `${label} is required`);

export const optionalString = z.string().optional();
