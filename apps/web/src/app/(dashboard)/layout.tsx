import Link from 'next/link';
import { type ReactNode } from 'react';

import { SignOutButton } from '../../components/auth/sign-out-button';
import { createClient } from '../../lib/supabase-server';

/**
 * Is anyone signed in?
 *
 * getUser validates the token with Supabase rather than trusting the cookie,
 * which is what the middleware does on every request already. A missing or
 * broken Supabase config answers "no" instead of throwing: the 3D viewer under
 * this layout is public, and it should still render for a visitor when auth is
 * the thing that is broken.
 */
async function isSignedIn(): Promise<boolean> {
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    return false;
  }
  try {
    const {
      data: { user },
    } = await createClient().auth.getUser();
    return user !== null;
  } catch {
    return false;
  }
}

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const signedIn = await isSignedIn();

  return (
    <div className="min-h-screen">
      <header className="bg-background/80 sticky top-0 z-50 border-b border-border backdrop-blur-md">
        <nav className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="TreeQ Carbon" className="h-8 w-8 object-contain" />
            <span className="font-display text-base font-bold tracking-tight">TreeQ Carbon</span>
          </Link>
          <div className="flex items-center gap-4 text-sm font-medium">
            <Link
              href="/dashboard"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/viewer"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              3D Viewer
            </Link>
            <SignOutButton signedIn={signedIn} />
          </div>
        </nav>
      </header>
      {children}
    </div>
  );
}
