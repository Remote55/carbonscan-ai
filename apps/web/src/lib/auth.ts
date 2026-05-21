/**
 * Auth helper functions — wraps Supabase Auth flows.
 *
 * Pattern: use Supabase JS SDK directly from Web (client + server).
 * Backend (FastAPI) verifies the JWT in subsequent API calls.
 */

import type { User } from '@supabase/supabase-js';
import { createClient } from './supabase';

export type AuthResult = {
  user: User | null;
  error: string | null;
};

/**
 * Sign up with email + password.
 * Sends a confirmation email by default (Supabase setting).
 */
export async function signUp(
  email: string,
  password: string,
  metadata?: { name?: string; role?: 'community' | 'industrial' | 'auditor' },
): Promise<AuthResult> {
  const supabase = createClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadata,
      emailRedirectTo: `${window.location.origin}/auth/callback`,
    },
  });

  return {
    user: data.user,
    error: error?.message ?? null,
  };
}

/**
 * Sign in with email + password.
 */
export async function signIn(email: string, password: string): Promise<AuthResult> {
  const supabase = createClient();
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  return {
    user: data.user,
    error: error?.message ?? null,
  };
}

/**
 * Sign out (clears session cookie).
 */
export async function signOut(): Promise<{ error: string | null }> {
  const supabase = createClient();
  const { error } = await supabase.auth.signOut();
  return { error: error?.message ?? null };
}

/**
 * Get the current session (browser-side).
 * Returns null if not signed in.
 */
export async function getSession() {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session;
}
