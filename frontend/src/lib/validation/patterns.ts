/**
 * Shared regex patterns for form validation.
 */

export const patterns = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  phone: /^\+?[\d\s()-]{7,}$/,
  url: /^https?:\/\/[^\s]+$/,
};
