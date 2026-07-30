'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { signOut } from '../../lib/auth';

/**
 * The way out.
 *
 * There was no sign-out control anywhere in the app - `signOut()` existed in
 * lib/auth.ts and nothing called it - so a teammate could sign in and then had no
 * way back out. Reported from real use, not caught by any test.
 *
 * `router.refresh()` after the redirect is load-bearing: the middleware decides
 * access from the session cookie on the server, and without a refresh the client
 * keeps rendering cached authenticated output even though the cookie is gone.
 */
/**
 * @param signedIn Decided by the server layout, which already validated the
 * session cookie. Asking the browser instead would render one control, resolve,
 * and swap it for the other - a header that visibly changes its mind about
 * whether it knows you, on the one page a judge is handed cold.
 */
export function SignOutButton({ signedIn }: { signedIn: boolean }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSignOut() {
    setPending(true);
    setError(null);

    const result = await signOut();
    if (result.error) {
      // Say so rather than navigating away and leaving the session intact, which
      // would look like a successful sign-out and is the more dangerous failure.
      setError('ออกจากระบบไม่สำเร็จ ลองอีกครั้ง');
      setPending(false);
      return;
    }

    router.replace('/');
    router.refresh();
  }

  // The 3D viewer is open to anyone now, so this header renders for visitors
  // who never signed in. Offering them a way out of a session they do not have
  // is worse than useless: this control is how someone tells whether they are
  // signed in at all.
  if (!signedIn) {
    return (
      <Link
        href="/login?redirect=%2Fdashboard%2Fviewer"
        className="rounded-full border border-border px-4 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        เข้าสู่ระบบ
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3">
      {error ? (
        <span role="alert" className="text-xs text-destructive">
          {error}
        </span>
      ) : null}
      <button
        type="button"
        onClick={handleSignOut}
        disabled={pending}
        aria-busy={pending}
        className="rounded-full border border-border px-4 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
      >
        {pending ? 'กำลังออกจากระบบ…' : 'ออกจากระบบ'}
      </button>
    </div>
  );
}
