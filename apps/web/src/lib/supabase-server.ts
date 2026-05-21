/**
 * Supabase clients for Next.js App Router server contexts.
 *
 * Use these in:
 * - Server Components
 * - Server Actions
 * - Route Handlers (API routes)
 * - Middleware
 *
 * For browser/Client Components, use `./supabase.ts` instead.
 */

import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

/**
 * Server client that reads/writes auth cookies via Next.js cookies() API.
 * Use in Server Components + Route Handlers.
 */
export function createClient() {
  const cookieStore = cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // setAll() in Server Components is a no-op (cookies are read-only).
            // Server Actions + Route Handlers can write — this throws there only
            // in older Next.js versions. Safe to swallow.
          }
        },
      },
    },
  );
}
