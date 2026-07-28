import type { AnalyzeResponse } from './api';
import type { RuntimeCredentials } from './demo-runtime';

export type UploadPhase = 'uploading' | 'processing';

export interface DemoApiClient {
  checkReadiness(): Promise<{ pipelineVersion: string }>;
  analyze(file: File, onPhase: (phase: UploadPhase) => void): Promise<AnalyzeResponse>;
}

export class DemoApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly publicDetail: string,
  ) {
    super(publicDetail);
    this.name = 'DemoApiError';
  }
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

function hexToBytes(hex: string): Uint8Array {
  return Uint8Array.from(hex.match(/.{2}/g) ?? [], (pair) => Number.parseInt(pair, 16));
}

function toArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  return copy.buffer as ArrayBuffer;
}

function proofMatches(expected: string, received: unknown): boolean {
  if (
    typeof received !== 'string' ||
    !/^[0-9a-f]{64}$/i.test(received) ||
    expected.length !== received.length
  ) {
    return false;
  }
  let difference = 0;
  for (let index = 0; index < expected.length; index += 1) {
    difference |= expected.charCodeAt(index) ^ received.charCodeAt(index);
  }
  return difference === 0;
}

async function createReadinessProof(token: string, challenge: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    'raw',
    toArrayBuffer(hexToBytes(token)),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const signature = await crypto.subtle.sign(
    'HMAC',
    key,
    toArrayBuffer(new TextEncoder().encode(challenge)),
  );
  return bytesToHex(new Uint8Array(signature));
}

function publicUploadDetail(status: number): string {
  return status >= 500 ? 'Analysis service is unavailable.' : 'Analysis request failed.';
}

export function createDemoApiClient(credentials: RuntimeCredentials): DemoApiClient {
  return {
    async checkReadiness() {
      try {
        const nonceBytes = crypto.getRandomValues(new Uint8Array(32));
        const challenge = bytesToHex(nonceBytes);
        const response = await fetch(new URL('/api/v1/health/demo-ready', credentials.endpoint), {
          method: 'GET',
          cache: 'no-store',
          headers: {
            'X-TreeQ-Demo-Token': credentials.token,
            'X-TreeQ-Demo-Challenge': challenge,
          },
        });
        if (!response.ok) throw new Error('Readiness response failed');

        const payload: unknown = await response.json();
        if (
          !payload ||
          typeof payload !== 'object' ||
          !('pipeline_version' in payload) ||
          !('challenge_hmac' in payload) ||
          typeof payload.pipeline_version !== 'string'
        ) {
          throw new Error('Readiness response was invalid');
        }

        const expectedProof = await createReadinessProof(credentials.token, challenge);
        if (!proofMatches(expectedProof, payload.challenge_hmac)) {
          throw new Error('Readiness proof was invalid');
        }
        return { pipelineVersion: payload.pipeline_version };
      } catch {
        throw new DemoApiError(0, 'Demo readiness failed');
      }
    },

    analyze(file, onPhase) {
      return new Promise<AnalyzeResponse>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append('file', file);

        onPhase('uploading');
        xhr.upload.onload = () => onPhase('processing');
        xhr.onload = () => {
          if (xhr.status < 200 || xhr.status >= 300) {
            reject(new DemoApiError(xhr.status, publicUploadDetail(xhr.status)));
            return;
          }
          try {
            resolve(JSON.parse(xhr.responseText) as AnalyzeResponse);
          } catch {
            reject(new DemoApiError(xhr.status, 'Analysis response was invalid.'));
          }
        };
        xhr.onerror = () => reject(new DemoApiError(0, 'Analysis service is unavailable.'));
        xhr.ontimeout = () => reject(new DemoApiError(0, 'Analysis service is unavailable.'));
        xhr.open('POST', new URL('/api/v1/upload/analyze', credentials.endpoint));
        xhr.setRequestHeader('X-TreeQ-Demo-Token', credentials.token);
        xhr.send(formData);
      });
    },
  };
}
