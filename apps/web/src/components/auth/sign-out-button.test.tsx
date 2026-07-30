import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: () => undefined, refresh: () => undefined }),
}));

const { SignOutButton } = await import('./sign-out-button');

describe('SignOutButton', () => {
  // There was no way out of the app at all: signOut() sat in lib/auth.ts and
  // nothing rendered a control for it, so a signed-in user was signed in for good.
  // This is the guard that the control exists and is a real button.
  it('renders an enabled sign-out control', () => {
    const markup = renderToStaticMarkup(<SignOutButton />);

    expect(markup).toContain('ออกจากระบบ');
    expect(markup).toContain('type="button"');
    // The rendered attribute, not the substring: the className carries
    // `disabled:opacity-50`, so a bare `not.toContain('disabled')` fails on
    // styling rather than on state.
    expect(markup).not.toContain('disabled=""');
    expect(markup).not.toContain('aria-busy="true"');
  });
});
