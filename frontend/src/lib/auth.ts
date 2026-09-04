/**
 * Auth helpers — token storage and access.
 *
 * Token is stored in localStorage (accessible to the auth hooks).
 * For production you would use httpOnly cookies + server-side middleware,
 * but localStorage is sufficient for this student project MVP.
 */

const TOKEN_KEY = "interviewpro_token";

export function saveToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function removeToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}
