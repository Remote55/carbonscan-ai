/**
 * Next.js middleware — refreshes Supabase session cookies on each request.
 *
 * Without this, the session cookie expires on the server even when the user
 * is still active on the client. Supabase docs recommend this exact pattern:
 * https://supabase.com/docs/guides/auth/server-side/nextjs
 */

import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          response = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // Refresh session — important: getUser() validates the JWT against Supabase,
  // unlike getSession() which trusts the cookie.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Protect /dashboard/* routes — redirect unauthenticated users to /login
  const url = request.nextUrl;
  const isProtected = url.pathname.startsWith('/dashboard');
  const isAuthPage = url.pathname.startsWith('/login') || url.pathname.startsWith('/signup');

  if (isProtected && !user) {
    const redirectUrl = url.clone();
    redirectUrl.pathname = '/login';
    redirectUrl.searchParams.set('redirect', url.pathname);
    return NextResponse.redirect(redirectUrl);
  }

  if (isAuthPage && user) {
    const redirectUrl = url.clone();
    redirectUrl.pathname = '/dashboard';
    return NextResponse.redirect(redirectUrl);
  }

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, logo.png (static assets)
     * - api routes (handled separately by Next API)
     */
    '/((?!_next/static|_next/image|favicon.ico|logo.png|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
