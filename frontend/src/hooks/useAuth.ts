"use client";
/**
 * useAuth hook — manages authentication state.
 *
 * Persists token in localStorage and exposes login/register/logout actions.
 * Components should use this hook instead of accessing localStorage directly.
 */
import { useState, useEffect, useCallback } from "react";
import { api, ApiError } from "@/lib/api-client";
import { getToken, saveToken, removeToken } from "@/lib/auth";
import type { TokenResponse, UserResponse } from "@/lib/types";

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  // Lazy init: if a stored token exists we start in loading state.
  const [state, setState] = useState<AuthState>(() => {
    const stored = typeof window !== "undefined" ? getToken() : null;
    return {
      user: null,
      token: stored,
      isLoading: stored !== null, // loading only if we have a token to validate
      error: null,
    };
  });

  // On mount, validate the stored token once.
  useEffect(() => {
    const stored = state.token;
    if (!stored) return; // nothing to validate

    let cancelled = false;
    api
      .authGet<UserResponse>("/api/v1/auth/me", stored)
      .then((user) => {
        if (!cancelled)
          setState({ user, token: stored, isLoading: false, error: null });
      })
      .catch(() => {
        if (!cancelled) {
          removeToken();
          setState({ user: null, token: null, isLoading: false, error: null });
        }
      });
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const data = await api.post<TokenResponse>("/api/v1/auth/login", {
          email,
          password,
        });
        saveToken(data.access_token);
        setState({
          user: data.user,
          token: data.access_token,
          isLoading: false,
          error: null,
        });
      } catch (err) {
        const msg =
          err instanceof ApiError ? err.message : "Login failed. Please try again.";
        setState((s) => ({ ...s, isLoading: false, error: msg }));
        throw err;
      }
    },
    []
  );

  const register = useCallback(
    async (
      email: string,
      password: string,
      fullName?: string
    ): Promise<void> => {
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const data = await api.post<TokenResponse>("/api/v1/auth/register", {
          email,
          password,
          full_name: fullName || null,
        });
        saveToken(data.access_token);
        setState({
          user: data.user,
          token: data.access_token,
          isLoading: false,
          error: null,
        });
      } catch (err) {
        const msg =
          err instanceof ApiError
            ? err.message
            : "Registration failed. Please try again.";
        setState((s) => ({ ...s, isLoading: false, error: msg }));
        throw err;
      }
    },
    []
  );

  const logout = useCallback(async (): Promise<void> => {
    const token = getToken();
    if (token) {
      await api.authPost("/api/v1/auth/logout", token).catch(() => {});
    }
    removeToken();
    setState({ user: null, token: null, isLoading: false, error: null });
  }, []);

  return {
    user: state.user,
    token: state.token,
    isLoading: state.isLoading,
    error: state.error,
    isAuthenticated: state.token !== null,
    login,
    register,
    logout,
  };
}
