/**
 * Middleware — protects /dashboard routes by checking access_token cookie.
 *
 * Fast-fail redirect to /login if cookie is missing. Full auth validation
 * happens server-side in the dashboard layout (layout.tsx checkAuth()).
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Guard /dashboard — require access_token cookie
  if (pathname.startsWith("/dashboard")) {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      const loginUrl = new URL("/login", request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  // Match everything except static files and api routes
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
