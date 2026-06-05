/**
 * Proxy route handler — forwards /media/* to Django on the same origin.
 *
 * A route handler (not next.config rewrites) is used on purpose: rewrites bake
 * their destination host at build time, but DJANGO_API_URL is only known at
 * runtime (compose service name). Reading process.env here keeps it runtime.
 */

import { NextRequest, NextResponse } from "next/server";

const DJANGO_API_URL = process.env.DJANGO_API_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const targetUrl = `${DJANGO_API_URL}/media/${path.join("/")}${request.nextUrl.search}`;

  const resp = await fetch(targetUrl, {
    // Forward cookies so the backend can authorize media once it serves it itself.
    headers: { cookie: request.headers.get("cookie") ?? "" },
    redirect: "manual",
  });

  const responseHeaders = new Headers(resp.headers);
  // The body stream is passed through as-is; drop length/encoding that fetch recomputes.
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  responseHeaders.delete("transfer-encoding");

  return new NextResponse(resp.body, {
    status: resp.status,
    statusText: resp.statusText,
    headers: responseHeaders,
  });
}
