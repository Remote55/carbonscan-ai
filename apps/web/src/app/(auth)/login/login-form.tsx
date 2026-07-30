'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { signIn } from '@/lib/auth';

export function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const redirectTo = params.get('redirect') ?? '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const result = await signIn(email, password);
    if (result.error) {
      setError(result.error);
      setLoading(false);
      return;
    }

    // `replace`, not `push`: with the session set, the middleware bounces /login
    // straight to /dashboard, so leaving login in the history means Back lands on
    // a page that immediately throws you forward again.
    router.replace(redirectTo);
    router.refresh();

    // Release the form even though we are navigating away. The success path used
    // to leave `loading` true forever, which disables every control on the page -
    // so if the navigation was slow or did not visibly happen, the user was left
    // on a screen where nothing could be clicked. A teammate reported exactly
    // that. Being able to press the button twice is a far smaller problem than
    // being locked out of the page.
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight">เข้าสู่ระบบ</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          ใส่อีเมลและรหัสผ่านของคุณเพื่อเข้าสู่ระบบ
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium">
            อีเมล
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-1.5 block text-sm font-medium">
            รหัสผ่าน
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div
            role="alert"
            className="border-destructive/30 bg-destructive/10 rounded-lg border px-3 py-2 text-sm text-destructive"
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="hover:bg-primary/90 inline-flex h-11 w-full items-center justify-center rounded-lg bg-primary px-6 text-sm font-medium text-primary-foreground transition-colors disabled:opacity-50"
        >
          {loading ? 'กำลังเข้าสู่ระบบ...' : 'เข้าสู่ระบบ'}
        </button>
      </form>

      <div className="text-center text-sm text-muted-foreground">
        ยังไม่มีบัญชี?{' '}
        <Link href="/signup" className="font-medium text-primary hover:underline">
          สมัครสมาชิก
        </Link>
      </div>
    </div>
  );
}
