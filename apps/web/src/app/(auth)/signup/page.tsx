'use client';

import Link from 'next/link';
import { useState } from 'react';
import { signUp } from '@/lib/auth';


export default function SignupPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Only the display name travels. Role is assigned by the database
    // trigger, which no longer reads anything the client sent.
    const result = await signUp(email, password, { name });
    if (result.error) {
      setError(result.error);
      setLoading(false);
      return;
    }

    setSuccess(true);
    setLoading(false);
    // If email confirmation is disabled in Supabase, user is signed in immediately.
    // Otherwise they need to click email link first.
  }

  if (success) {
    return (
      <div className="space-y-4 text-center">
        <h1 className="font-display text-2xl font-bold">ตรวจอีเมลของคุณ ✉</h1>
        <p className="text-sm text-muted-foreground">
          เราส่งลิงก์ยืนยันไปที่ <strong>{email}</strong> แล้ว
          <br />
          คลิกลิงก์ในอีเมลเพื่อเปิดใช้งานบัญชี
        </p>
        <Link
          href="/login"
          className="inline-block text-sm font-medium text-primary hover:underline"
        >
          กลับไปหน้าเข้าสู่ระบบ
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight">สมัครสมาชิก</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          เริ่มต้นใช้งานฟรี — สแกนต้นไม้ของคุณวันนี้
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="mb-1.5 block text-sm font-medium">
            ชื่อ
          </label>
          <input
            id="name"
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="สมชาย ใจดี"
          />
        </div>

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
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="••••••••"
          />
          <p className="mt-1 text-xs text-muted-foreground">อย่างน้อย 8 ตัวอักษร</p>
        </div>

        {/* The role selector is gone. It wrote straight into the signup
            metadata that the database trigger read to set public.users.role,
            so "Auditor" in a dropdown granted the right to mark any tree
            verified — the trust anchor of the whole product — and the same
            field accepted 'admin' from anyone editing the request. The trigger
            now assigns 'community' to everyone regardless, so leaving the
            control on screen would only promise something it no longer does. */}

        {error && (
          <div
            role="alert"
            className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="inline-flex h-11 w-full items-center justify-center rounded-lg bg-primary px-6 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? 'กำลังสมัคร...' : 'สมัครสมาชิกฟรี'}
        </button>
      </form>

      <div className="text-center text-sm text-muted-foreground">
        มีบัญชีแล้ว?{' '}
        <Link href="/login" className="font-medium text-primary hover:underline">
          เข้าสู่ระบบ
        </Link>
      </div>
    </div>
  );
}
