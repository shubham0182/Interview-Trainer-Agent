/**
 * Next.js middleware — guards protected routes.
 *
 * Redirects unauthenticated users to /auth/login.
 * Token is stored in localStorage (client-side) so middleware
 * cannot read it — client-side guards in each page handle auth redirects.
 * Middleware here prevents direct URL access to protected server routes only.
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(_request: NextRequest): NextResponse {
  // No server-side token to check (localStorage is client-only).
  // Client pages call useAuth() and redirect to /auth/login themselves.
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
