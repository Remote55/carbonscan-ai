'use client';

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
export function SignOutButton() {
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
