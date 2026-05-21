/**
 * Auth callback route — handles redirects from Supabase email confirmation
 * and OAuth providers.
 *
 * Supabase sends users here with a `code` query param after they click the
 * confirmation link in their email. We exchange the code for a session.
 */

import { createClient } from '@/lib/supabase-server';
import { NextResponse, type NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = searchParams.get('next') ?? '/dashboard';

  if (code) {
    const supabase = createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // No code or exchange failed → send back to login with error
  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}
