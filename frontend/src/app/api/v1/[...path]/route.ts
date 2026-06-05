/**
 * Proxy route handler — forwards /api/v1/* to Django on the same origin.
 *
 * Rewrites cookie paths from /api/ → / so the browser attaches JWT cookies
 * to all frontend routes.
 */

import { NextRequest, NextResponse } from "next/server";

const DJANGO_API_URL = process.env.DJANGO_API_URL || "http://localhost:8000";

async function proxyRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const targetUrl = `${DJANGO_API_URL}/api/v1/${path.join("/")}/${request.nextUrl.search}`;

  const forwardHeaders = new Headers(request.headers);
  // Let fetch recompute these for the upstream request.
  forwardHeaders.delete("host");
  forwardHeaders.delete("content-length");

  const hasBody = !["GET", "HEAD"].includes(request.method);
  const init: RequestInit = {
    method: request.method,
    headers: forwardHeaders,
    // arrayBuffer is binary-safe — handles JSON and multipart (image/PDF) alike.
    body: hasBody ? await request.arrayBuffer() : undefined,
    redirect: "manual",
  };

  const resp = await fetch(targetUrl, init);

  const responseHeaders = new Headers(resp.headers);
  // The body is already decoded by fetch; drop headers that would mismatch it.
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  responseHeaders.delete("transfer-encoding");

  // Login sets multiple cookies (access + refresh); getSetCookie returns each
  // separately (get("set-cookie") would merge them and break parsing).
  responseHeaders.delete("set-cookie");
  for (const cookie of resp.headers.getSetCookie()) {
    responseHeaders.append("set-cookie", cookie.replace(/Path=\/api[^;]*/gi, "Path=/"));
  }

  return new NextResponse(resp.body, {
    status: resp.status,
    statusText: resp.statusText,
    headers: responseHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
