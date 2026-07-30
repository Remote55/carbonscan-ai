export type RuntimeCredentials = Readonly<{ endpoint: string; token: string }>;

export const RUNTIME_STORAGE_KEY = 'treeq.demo.runtime.v1';

export interface RuntimeBrowser {
  location: Pick<Location, 'hash' | 'pathname'>;
  history: Pick<History, 'replaceState'>;
  storage: Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
}

const DEMO_TUNNEL_HOST = /^[a-z0-9-]+\.trycloudflare\.com$/i;
const DEMO_TOKEN = /^[0-9a-fA-F]{64}$/;

export function validateDemoEndpoint(rawEndpoint: string): string | null {
  if (rawEndpoint.includes('?') || rawEndpoint.includes('#')) return null;

  let endpoint: URL;
  try {
    endpoint = new URL(rawEndpoint);
  } catch {
    return null;
  }

  if (
    endpoint.username ||
    endpoint.password ||
    endpoint.search ||
    endpoint.hash ||
    endpoint.pathname !== '/'
  ) {
    return null;
  }

  const isTunnel =
    endpoint.protocol === 'https:' &&
    endpoint.port === '' &&
    DEMO_TUNNEL_HOST.test(endpoint.hostname);
  const isLocal =
    endpoint.protocol === 'http:' &&
    (endpoint.hostname === '127.0.0.1' || endpoint.hostname === 'localhost') &&
    endpoint.port === '8000';

  return isTunnel || isLocal ? endpoint.origin : null;
}

function parseCredentials(serialized: string): RuntimeCredentials | null {
  try {
    const parsed: unknown = JSON.parse(serialized);
    if (
      !parsed ||
      typeof parsed !== 'object' ||
      !('endpoint' in parsed) ||
      !('token' in parsed) ||
      typeof parsed.endpoint !== 'string' ||
      typeof parsed.token !== 'string'
    ) {
      return null;
    }
    const endpoint = validateDemoEndpoint(parsed.endpoint);
    return endpoint && DEMO_TOKEN.test(parsed.token) ? { endpoint, token: parsed.token } : null;
  } catch {
    return null;
  }
}

function scrubHandoff(browser: RuntimeBrowser): void {
  // Strip the fragment without moving the visitor. This used to hard-code
  // /demo, which was harmless while /demo was the only page that read a
  // handoff - and became a redirect the moment the viewer read one too.
  browser.history.replaceState(null, '', browser.location.pathname);
}

/**
 * The credentials already stored for this tab, without touching the fragment.
 *
 * consumeRuntimeHandoff is the entry point: a page calls it once on mount, and
 * it is what writes the store. This is the read side, for callers that need the
 * endpoint on every request rather than once per page - the API client, which
 * has no mount to hang a handoff off.
 */
export function readRuntimeCredentials(
  storage: Pick<Storage, 'getItem'>,
): RuntimeCredentials | null {
  return parseCredentials(storage.getItem(RUNTIME_STORAGE_KEY) ?? '');
}

export function consumeRuntimeHandoff(browser: RuntimeBrowser): RuntimeCredentials | null {
  const fragment = browser.location.hash;
  if (!fragment) {
    return parseCredentials(browser.storage.getItem(RUNTIME_STORAGE_KEY) ?? '');
  }

  scrubHandoff(browser);
  const params = new URLSearchParams(fragment.slice(1));
  const endpoints = params.getAll('api');
  const tokens = params.getAll('token');
  const hasOnlyExpectedParameters = [...params.keys()].every(
    (key) => key === 'api' || key === 'token',
  );
  const endpoint = endpoints.length === 1 ? validateDemoEndpoint(endpoints[0]) : null;
  const token = tokens.length === 1 && DEMO_TOKEN.test(tokens[0]) ? tokens[0] : null;

  if (!hasOnlyExpectedParameters || !endpoint || !token) {
    browser.storage.removeItem(RUNTIME_STORAGE_KEY);
    return null;
  }

  const credentials: RuntimeCredentials = { endpoint, token };
  browser.storage.setItem(RUNTIME_STORAGE_KEY, JSON.stringify(credentials));
  return credentials;
}
