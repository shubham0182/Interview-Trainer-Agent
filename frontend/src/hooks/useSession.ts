"use client";
/**
 * useSession hook — manages live interview session state and polling.
 * Full implementation in ST-17.
 */
export function useSession(sessionId: string) {
  void sessionId; // used in ST-17
  return {
    session: null,
    currentQuestion: null,
    isLoading: false,
    error: null,
  };
}
