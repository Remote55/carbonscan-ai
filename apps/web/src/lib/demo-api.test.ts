import { afterEach, describe, expect, it, vi } from 'vitest';

import { createDemoApiClient, DemoApiError } from './demo-api';
import type { RuntimeCredentials } from './demo-runtime';

const credentials: RuntimeCredentials = {
  endpoint: 'https://green-tree.trycloudflare.com',
  token: '00'.repeat(32),
};

describe('createDemoApiClient().checkReadiness', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sends a challenge in headers and accepts only a matching HMAC proof', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        pipeline_version: 'tlsep-v1',
        challenge_hmac: '569df9c32e65fe631753093848364f9075bf07654e4dcf9a5bfa2a1c904d5f06',
      }),
    }));
    vi.stubGlobal('fetch', fetchMock);
    vi.stubGlobal('crypto', {
      getRandomValues: (bytes: Uint8Array) => {
        bytes.set(Array.from({ length: 32 }, (_, index) => index));
        return bytes;
      },
      subtle: globalThis.crypto.subtle,
    });

    const result = await createDemoApiClient(credentials).checkReadiness();

    const [url, init] = fetchMock.mock.calls[0] as unknown as [URL, RequestInit];
    expect(String(url)).toBe('https://green-tree.trycloudflare.com/api/v1/health/demo-ready');
    expect(String(url)).not.toContain(credentials.token);
    expect(new Headers(init.headers).get('X-TreeQ-Demo-Token')).toBe(credentials.token);
    expect(new Headers(init.headers).get('X-TreeQ-Demo-Challenge')).toBe(
      '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f',
    );
    expect(result).toEqual({ pipelineVersion: 'tlsep-v1' });
  });

  it('rejects readiness when the server proof is not valid', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => ({ pipeline_version: 'tlsep-v1', challenge_hmac: '00'.repeat(32) }),
      })),
    );

    await expect(createDemoApiClient(credentials).checkReadiness()).rejects.toThrow(
      'Demo readiness failed',
    );
  });
});

describe('createDemoApiClient().analyze', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('reports upload and processing phases while sending the token only as a header', async () => {
    const opened: string[] = [];
    const sentHeaders = new Map<string, string>();
    class FakeXmlHttpRequest {
      readonly upload = { onload: null as (() => void) | null };
      status = 200;
      responseText = JSON.stringify({
        metadata: { pipeline_version: 'tlsep-v1' },
        summary: {},
        trees: [],
      });
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;

      open(_method: string, url: URL) {
        opened.push(String(url));
      }
      setRequestHeader(name: string, value: string) {
        sentHeaders.set(name, value);
      }
      send() {
        this.upload.onload?.();
        this.onload?.();
      }
    }
    vi.stubGlobal('XMLHttpRequest', FakeXmlHttpRequest);

    const phases: string[] = [];
    const result = await createDemoApiClient(credentials).analyze(
      new File(['point-cloud'], 'plot.ply'),
      (phase) => phases.push(phase),
    );

    expect(opened).toEqual(['https://green-tree.trycloudflare.com/api/v1/upload/analyze']);
    expect(opened[0]).not.toContain(credentials.token);
    expect(sentHeaders.get('X-TreeQ-Demo-Token')).toBe(credentials.token);
    expect(phases).toEqual(['uploading', 'processing']);
    expect(result.metadata.pipeline_version).toBe('tlsep-v1');
  });

  it('maps failed uploads to a public error that never includes token material', async () => {
    class FailedXmlHttpRequest {
      readonly upload = { onload: null as (() => void) | null };
      status = 503;
      responseText = JSON.stringify({ detail: credentials.token });
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;

      open() {}
      setRequestHeader() {}
      send() {
        this.onload?.();
      }
    }
    vi.stubGlobal('XMLHttpRequest', FailedXmlHttpRequest);

    await expect(
      createDemoApiClient(credentials).analyze(new File(['x'], 'plot.ply'), () => undefined),
    ).rejects.toBeInstanceOf(DemoApiError);
    await expect(
      createDemoApiClient(credentials).analyze(new File(['x'], 'plot.ply'), () => undefined),
    ).rejects.not.toThrow(credentials.token);
  });
});
