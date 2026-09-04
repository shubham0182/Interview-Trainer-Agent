/**
 * Centralised API client.
 *
 * All backend requests go through `api.*` helpers here.
 * Never use raw fetch() in components or hooks.
 */

const API_BASE =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
    /\/$/,
    ""
  );

// ── Error type ────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? "Request failed");
  }

  // 204 No Content has no body
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

// ── Auth helpers ──────────────────────────────────────────────────────────────

function withAuth(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

// ── Public API surface ────────────────────────────────────────────────────────

export const api = {
  /** POST — unauthenticated */
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),

  /** POST — authenticated */
  authPost: <T>(path: string, token: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      headers: withAuth(token),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  /** GET — authenticated */
  authGet: <T>(path: string, token: string) =>
    request<T>(path, { method: "GET", headers: withAuth(token) }),

  /** PUT — authenticated */
  authPut: <T>(path: string, token: string, body: unknown) =>
    request<T>(path, {
      method: "PUT",
      headers: withAuth(token),
      body: JSON.stringify(body),
    }),
};
