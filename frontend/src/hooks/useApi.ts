/**
 * useApi — thin wrapper around fetch() pointing at /api/v1/*.
 *
 * Always uses same-origin proxy. Cookies attach
 * automatically; no Authorization header needed for web clients.
 */

"use client";

import { useCallback } from "react";

type FetchOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

/**
 * Pull a human message from an error body. Handles both DRF shapes:
 *   { detail: "..." }              non-field errors (e.g. login)
 *   { field: ["msg", ...], ... }   field-level validation (e.g. register)
 */
function extractErrorMessage(data: unknown, status: number): string {
  if (typeof data === "object" && data !== null) {
    const obj = data as Record<string, unknown>;
    if (typeof obj.detail === "string") return obj.detail;
    for (const value of Object.values(obj)) {
      const msg = Array.isArray(value) ? value[0] : value;
      if (typeof msg === "string") return msg;
    }
  }
  return `HTTP ${status}`;
}

export function useApi() {
  const fetchApi = useCallback(
    async <T = unknown>(
      path: string,
      options: FetchOptions = {},
    ): Promise<T> => {
      const { method = "GET", body, signal, headers = {} } = options;

      const resp = await fetch(`/api/v1${path}`, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
        credentials: "include",
      });

      if (resp.status === 204) {
        return undefined as T;
      }

      const contentType = resp.headers.get("content-type") || "";
      const data = contentType.includes("application/json")
        ? await resp.json()
        : await resp.text();

      if (!resp.ok) {
        throw new ApiError(resp.status, extractErrorMessage(data, resp.status), data);
      }

      return data as T;
    },
    [],
  );

  return { fetchApi };
}
