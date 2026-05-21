import { Suspense } from 'react';
import { LoginForm } from './login-form';

/**
 * Login page — Server Component wrapper.
 *
 * The actual form is in login-form.tsx (Client Component using
 * useSearchParams). Wrapping it in <Suspense> here lets Next.js
 * prerender this page statically (the form streams in client-side).
 */
export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFormFallback />}>
      <LoginForm />
    </Suspense>
  );
}

function LoginFormFallback() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight">เข้าสู่ระบบ</h1>
        <p className="mt-2 text-sm text-muted-foreground">กำลังโหลด...</p>
      </div>
    </div>
  );
}
