import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';

/**
 * A confirmation link that fails sends the visitor to /login with
 * ?error=auth_callback_failed. Nothing on the page read it, so they arrived at
 * an ordinary-looking login form with no message, no way to request another
 * link, and an account that could never be confirmed.
 */

function renderWith(search: string) {
  vi.resetModules();
  vi.doMock('next/navigation', () => ({
    useRouter: () => ({ replace: vi.fn(), refresh: vi.fn() }),
    useSearchParams: () => new URLSearchParams(search),
  }));
  vi.doMock('@/lib/auth', () => ({
    signIn: vi.fn(),
    resendConfirmation: vi.fn(),
  }));
  return import('./login-form').then(({ LoginForm }) =>
    renderToStaticMarkup(<LoginForm />),
  );
}

describe('a failed confirmation link', () => {
  it('is explained instead of arriving silently', async () => {
    const markup = await renderWith('error=auth_callback_failed');

    expect(markup).toContain('ลิงก์ยืนยันอีเมลใช้ไม่ได้');
  });

  it('offers a way out', async () => {
    const markup = await renderWith('error=auth_callback_failed');

    expect(markup).toContain('ส่งลิงก์ยืนยันใหม่');
  });

  it('says nothing when the visitor simply came to sign in', async () => {
    const markup = await renderWith('');

    expect(markup).not.toContain('ลิงก์ยืนยันอีเมลใช้ไม่ได้');
  });

  it('is not triggered by some other error value', async () => {
    const markup = await renderWith('error=something_else');

    expect(markup).not.toContain('ลิงก์ยืนยันอีเมลใช้ไม่ได้');
  });
});
