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
 * Where a confirmation email should send its reader back to.
 *
 * `window.location.origin` on its own is wrong here, and a teammate found out the
 * hard way: it bakes whichever origin happened to be open at signup into a link
 * that gets opened later, usually on a different device. Signing up against a dev
 * server produced emails pointing every recipient at http://localhost:3000, which
 * resolves only on the machine that sent them - on an iPad it is
 * ERR_CONNECTION_FAILED and the account can never be confirmed.
 *
 * NEXT_PUBLIC_SITE_URL pins the canonical origin so deployed signups always link
 * to the deployed site. Local development leaves it unset and keeps the current
 * origin, so that flow still works.
 *
 * Supabase also has to allow the resulting URL: if it is not in the project's
 * Redirect URLs list, Supabase silently substitutes the project Site URL, which
 * is `http://localhost:3000` on a fresh project. Setting this variable is not
 * enough on its own.
 */
export function authRedirectOrigin(): string {
  const configured = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configured) return configured.replace(/\/+$/, '');
  return window.location.origin;
}

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
      emailRedirectTo: `${authRedirectOrigin()}/auth/callback`,
    },
  });

  return {
    user: data.user,
    error: error?.message ?? null,
  };
}

/**
 * Send the confirmation email again.
 *
 * A confirmation link can fail for reasons the person who clicked it cannot do
 * anything about: it expired, it was already used, or the deployment's redirect
 * URL was wrong when the account was created. Before this existed the callback
 * sent them to /login with an error nothing displayed, and there was no way
 * forward at all — the account could never be confirmed and never be used.
 */
export async function resendConfirmation(email: string): Promise<AuthResult> {
  const supabase = createClient();
  const { error } = await supabase.auth.resend({
    type: 'signup',
    email,
    options: { emailRedirectTo: `${authRedirectOrigin()}/auth/callback` },
  });

  return { user: null, error: error?.message ?? null };
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
