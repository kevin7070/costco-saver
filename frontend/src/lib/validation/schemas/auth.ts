import { z } from "zod";

import { emailSchema, requiredString } from "../refinements";

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
});

export type LoginForm = z.infer<typeof loginSchema>;

export const changePasswordSchema = z.object({
  current_password: z.string().min(1, "Current password is required"),
  new_password: z.string().min(8, "New password must be at least 8 characters"),
});

export type ChangePasswordForm = z.infer<typeof changePasswordSchema>;

export const registerSchema = z
  .object({
    first_name: requiredString("First name"),
    last_name: requiredString("Last name"),
    email: emailSchema,
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: requiredString("Password confirmation"),
    website: z.string().optional().default(""), // honeypot — must stay empty
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type RegisterForm = z.infer<typeof registerSchema>;

export const forgotPasswordSchema = z.object({
  email: emailSchema,
});

export type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: requiredString("Password confirmation"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;
