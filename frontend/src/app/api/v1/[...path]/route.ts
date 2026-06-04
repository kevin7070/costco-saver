/**
 * Proxy route handler — forwards /api/v1/* to Django on the same origin.
 *
 * Rewrites cookie paths from /api/ → /
 * so the browser attaches JWT cookies to all frontend routes.
 */

import { NextRequest, NextResponse } from "next/server";

const DJANGO_API_URL = process.env.DJANGO_API_URL || "http://localhost:8000";

async function proxyRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const targetPath = path.join("/");
  const search = request.nextUrl.search;
  const targetUrl = `${DJANGO_API_URL}/api/v1/${targetPath}/${search}`;

  // Forward headers but override host to the internal target
  const forwardHeaders = new Headers(request.headers);
  forwardHeaders.set("host", new URL(DJANGO_API_URL).host);

  const init: RequestInit = {
    method: request.method,
    headers: forwardHeaders,
    body: ["GET", "HEAD"].includes(request.method)
      ? undefined
      : await request.text(),
    redirect: "manual",
  };

  const resp = await fetch(targetUrl, init);

  // Rewrite cookie paths from /api/ → /
  const responseHeaders = new Headers(resp.headers);
  const setCookie = resp.headers.get("set-cookie");
  if (setCookie) {
    const rewritten = setCookie.replace(/Path=\/api[^;]*/gi, "Path=/");
    responseHeaders.set("set-cookie", rewritten);
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
