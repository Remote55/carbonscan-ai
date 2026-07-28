/**
 * Next.js middleware — refreshes Supabase session cookies on each request.
 *
 * Without this, the session cookie expires on the server even when the user
 * is still active on the client. Supabase docs recommend this exact pattern:
 * https://supabase.com/docs/guides/auth/server-side/nextjs
 */

import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

type CookieSetItem = { name: string; value: string; options: CookieOptions };

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (pathname === '/demo' || pathname.startsWith('/demo/')) {
    return NextResponse.next({ request });
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // No Supabase env → skip auth handling entirely. Lets local `npm run dev`
  // render public pages without secrets, and makes production degrade
  // gracefully (no 500 on every request) if the env is ever missing, instead
  // of throwing inside createServerClient.
  if (!supabaseUrl || !supabaseAnonKey) {
    return NextResponse.next({ request });
  }

  let response = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    supabaseUrl,
    supabaseAnonKey,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet: CookieSetItem[]) {
          cookiesToSet.forEach(({ name, value }: CookieSetItem) =>
            request.cookies.set(name, value),
          );
          response = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }: CookieSetItem) =>
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
  const isProtected = pathname.startsWith('/dashboard');
  const isAuthPage = pathname.startsWith('/login') || pathname.startsWith('/signup');

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
