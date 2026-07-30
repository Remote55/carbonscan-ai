import { describe, expect, it, vi } from 'vitest';

import {
  consumeRuntimeHandoff,
  readRuntimeCredentials,
  RUNTIME_STORAGE_KEY,
  validateDemoEndpoint,
} from './demo-runtime';

function makeFakeBrowser(hash: string, pathname = '/demo') {
  const values = new Map<string, string>();
  return {
    location: { hash, pathname },
    history: { replaceState: vi.fn() },
    storage: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    },
  };
}

describe('validateDemoEndpoint', () => {
  it('accepts only exact demo origins', () => {
    expect(validateDemoEndpoint('https://green-tree.trycloudflare.com')).toBe(
      'https://green-tree.trycloudflare.com',
    );
    expect(validateDemoEndpoint('https://evil.trycloudflare.com.attacker.test')).toBeNull();
    expect(validateDemoEndpoint('http://127.0.0.1:8000')).toBe('http://127.0.0.1:8000');
    expect(validateDemoEndpoint('http://localhost:8000')).toBe('http://localhost:8000');
    expect(validateDemoEndpoint('http://127.0.0.1:9000')).toBeNull();
  });

  it('rejects endpoint components beyond an allowed origin', () => {
    expect(validateDemoEndpoint('https://user@green-tree.trycloudflare.com')).toBeNull();
    expect(validateDemoEndpoint('https://green-tree.trycloudflare.com/api')).toBeNull();
    expect(validateDemoEndpoint('https://green-tree.trycloudflare.com?next=/demo')).toBeNull();
    expect(validateDemoEndpoint('https://green-tree.trycloudflare.com#fragment')).toBeNull();
    expect(validateDemoEndpoint('https://green-tree.trycloudflare.com/?')).toBeNull();
    expect(validateDemoEndpoint('https://green-tree.trycloudflare.com/#')).toBeNull();
  });
});

describe('consumeRuntimeHandoff', () => {
  it('stores a valid fragment once and scrubs history', () => {
    const browser = makeFakeBrowser(
      '#api=https%3A%2F%2Fgreen-tree.trycloudflare.com&token=' + 'a'.repeat(64),
    );

    const credentials = consumeRuntimeHandoff(browser);

    expect(credentials?.token).toBe('a'.repeat(64));
    expect(browser.history.replaceState).toHaveBeenCalledWith(null, '', '/demo');
    expect(browser.storage.getItem(RUNTIME_STORAGE_KEY)).not.toBeNull();
  });

  it('does not retain malformed handoff credentials', () => {
    const browser = makeFakeBrowser('#api=http%3A%2F%2F127.0.0.1%3A9000&token=not-hex');

    expect(consumeRuntimeHandoff(browser)).toBeNull();
    expect(browser.storage.getItem(RUNTIME_STORAGE_KEY)).toBeNull();
    expect(browser.history.replaceState).toHaveBeenCalledWith(null, '', '/demo');
  });

  it('leaves the visitor on the page that received the handoff', () => {
    // The scrub used to send every handoff to /demo, so a launcher link opened
    // on the viewer bounced the visitor off the page they asked for.
    const browser = makeFakeBrowser(
      '#api=https%3A%2F%2Fgreen-tree.trycloudflare.com&token=' + 'b'.repeat(64),
      '/dashboard/viewer',
    );

    expect(consumeRuntimeHandoff(browser)?.endpoint).toBe('https://green-tree.trycloudflare.com');
    expect(browser.history.replaceState).toHaveBeenCalledWith(null, '', '/dashboard/viewer');
  });
});

describe('readRuntimeCredentials', () => {
  it('returns what a consumed handoff stored, without a fragment present', () => {
    const source = makeFakeBrowser(
      '#api=https%3A%2F%2Fgreen-tree.trycloudflare.com&token=' + 'c'.repeat(64),
    );
    consumeRuntimeHandoff(source);

    expect(readRuntimeCredentials(source.storage)).toEqual({
      endpoint: 'https://green-tree.trycloudflare.com',
      token: 'c'.repeat(64),
    });
  });

  it('refuses a stored endpoint that would not survive validation', () => {
    // Storage is writable by anything running on the origin, so what comes back
    // out is re-checked rather than trusted for having once been checked.
    const storage = {
      getItem: () =>
        JSON.stringify({ endpoint: 'https://attacker.test', token: 'd'.repeat(64) }),
    };

    expect(readRuntimeCredentials(storage)).toBeNull();
  });

  it('is null when nothing was handed off', () => {
    expect(readRuntimeCredentials({ getItem: () => null })).toBeNull();
  });
});
