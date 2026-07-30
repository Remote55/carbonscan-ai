/**
 * API client for TreeQ Carbon Platform Backend (FastAPI).
 *
 * Uses native fetch with type-safe wrappers.
 * Auth token automatically attached if present in localStorage.
 */

import { readRuntimeCredentials } from './demo-runtime';
import { createClient } from './supabase';

const BUILT_IN_API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

/**
 * The demo token this deployment was built with, published alongside the tunnel
 * URL on every Auto run.
 *
 * It is deliberately public. The API's upload guard wants a token, and a
 * visitor who simply opens the site was never handed one - so without this, the
 * only person who could run an analysis is whoever is sitting at the laptop
 * that started the launcher, which defeats the point of deploying at all.
 *
 * What it still buys: the guard turns away anything that finds the tunnel
 * hostname without reading the site, and the per-client rate limit behind it is
 * unchanged. The token rotates every run, so it is a key to one demo session
 * rather than a standing credential.
 */
const BUILT_IN_DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN || null;

const ENV_API_CONFIGURED =
  typeof process.env.NEXT_PUBLIC_API_URL === 'string' &&
  process.env.NEXT_PUBLIC_API_URL.length > 0 &&
  !process.env.NEXT_PUBLIC_API_URL.includes('localhost');

type Backend = Readonly<{ url: string; demoToken: string | null }>;

/**
 * Where to send this request, decided per call rather than at build time.
 *
 * NEXT_PUBLIC_* is baked in when the site is built, but a quick tunnel gets a
 * new hostname every time it starts. A deployed page pinned to one of those
 * hostnames is pointing at a dead backend by the second run, which is exactly
 * what happened: the viewer kept calling a tunnel that no longer existed.
 *
 * So prefer the runtime handoff the launcher already hands to /demo. It is
 * validated on the way in - only a trycloudflare host or 127.0.0.1:8000 is
 * accepted - and it travels with the visitor, so anyone who opens the launcher
 * link reaches whichever backend is live right now, with no redeploy.
 */
function resolveBackend(): Backend {
  if (typeof window !== 'undefined') {
    const runtime = readRuntimeCredentials(window.sessionStorage);
    if (runtime) return { url: runtime.endpoint, demoToken: runtime.token };
  }
  return { url: BUILT_IN_API_URL, demoToken: BUILT_IN_DEMO_TOKEN };
}

/**
 * True when this browser can actually reach a backend right now.
 *
 * A function, not a constant: a handoff can arrive after the module loads, and
 * a constant captured at import time would answer for the wrong moment. Callers
 * use it to explain themselves up front instead of letting someone press a
 * button that can only fail.
 */
export function isApiConfigured(): boolean {
  if (typeof window !== 'undefined' && readRuntimeCredentials(window.sessionStorage)) {
    return true;
  }
  return ENV_API_CONFIGURED;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

type RequestOptions = RequestInit & {
  params?: Record<string, string | number | boolean | undefined>;
};

/** Bearer token for authenticated endpoints (Supabase session; browser only). */
async function getAccessToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null;
  try {
    const { data } = await createClient().auth.getSession();
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...init } = options;

  const backend = resolveBackend();

  // Build URL with query params
  const url = new URL(`/api/v1${path}`, backend.url);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  // Attach the Supabase session token for authenticated endpoints (e.g. /jobs)
  const headers = new Headers(init.headers);
  const token = await getAccessToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  // The demo API guards its synchronous upload route with this header. It is a
  // separate secret from the Supabase session: one says who the visitor is, the
  // other says this browser was handed the running demo.
  if (backend.demoToken) headers.set('x-treeq-demo-token', backend.demoToken);

  // Default content type for JSON requests
  if (init.body && !headers.has('Content-Type') && typeof init.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, { ...init, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, response.statusText, body);
  }

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'GET' }),

  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),

  /** Upload FormData (e.g., file uploads). */
  upload: <T>(path: string, formData: FormData, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: 'POST',
      body: formData,
      // Don't set Content-Type — browser sets it automatically with boundary
    }),
};

export { ApiError };

// --- Point-cloud analysis (sync MVP: POST /api/v1/upload/analyze) ---

export interface AnalyzeTree {
  tree_id: number;
  species_sci: string | null;
  dbh_cm: number;
  height_m: number;
  volume_m3: number | null;
  biomass_kg: number | null;
  carbon_kg: number | null;
  co2eq_kg: number | null;
  location: Record<string, number>;
  point_count: number;
}

/** Why a detected segment produced no measurement. */
export type ExcludedReasonCode = 'WOOD_EMPTY' | 'QSM_INVALID';

export interface AnalyzeExcludedSegment {
  tree_id: number;
  stage: 'wood_leaf' | 'qsm';
  reason_code: ExcludedReasonCode;
}

export interface AnalyzeDiagnostics {
  excluded_segments: AnalyzeExcludedSegment[];
}

export interface AnalyzeSummary {
  total_trees: number;
  total_carbon_kg: number;
  total_co2eq_kg: number;
  /**
   * Added in pipeline 0.4.0, so optional: results stored by 0.3.0 have no
   * counts. Undefined means "this run did not report it" — never render it as
   * zero, or an old result reads as though nothing was excluded.
   */
  detected_trees?: number | null;
  measured_trees?: number | null;
  excluded_trees?: number | null;
}

export interface AnalyzeMetadata {
  pipeline_version: string;
  git_commit: string;
  git_dirty: boolean;
  wood_leaf_backend: string;
  input_sha256: string;
  checkpoint_sha256: string | null;
  algorithms: Record<string, string>;
  evidence_status: string;
  candidate_status: string;
  n_input_points: number;
  status: string;
  input_file?: string | null;
}

export interface AnalyzeResponse {
  metadata: AnalyzeMetadata;
  summary: AnalyzeSummary;
  trees: AnalyzeTree[];
  diagnostics?: AnalyzeDiagnostics | null;
}

/** Upload a point-cloud file to the backend, run the pipeline, get carbon results. */
export function analyzePointCloud(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return api.upload<AnalyzeResponse>('/upload/analyze', formData);
}

// --- Async jobs (POST /jobs/analyze -> poll GET /jobs/{id}) ---
// Non-blocking path: submit returns a job id immediately, a worker processes it
// in the background. Requires auth + a deployed API/worker.

export interface JobCreated {
  id: string;
  status: string;
  created_at: string;
}

export interface JobDetail {
  id: string;
  status: string; // queued | processing | completed | failed | cancelled
  progress: number;
  total_trees_detected: number | null;
  total_carbon_kg: number | null;
  result: AnalyzeResponse | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

const TERMINAL_JOB_STATUSES = new Set(['completed', 'failed', 'cancelled']);

/** Submit a point cloud as an async job (requires auth). Returns immediately. */
export function submitAnalyzeJob(file: File): Promise<JobCreated> {
  const formData = new FormData();
  formData.append('file', file);
  return api.upload<JobCreated>('/jobs/analyze', formData);
}

/** Fetch one job's status + result (owner only). */
export function getJob(id: string): Promise<JobDetail> {
  return api.get<JobDetail>(`/jobs/${id}`);
}

/** Poll a job until it reaches a terminal status (completed/failed/cancelled). */
export async function pollJobUntilDone(
  id: string,
  opts: { intervalMs?: number; timeoutMs?: number; onUpdate?: (job: JobDetail) => void } = {},
): Promise<JobDetail> {
  const { intervalMs = 2000, timeoutMs = 600_000, onUpdate } = opts;
  const start = Date.now();
  for (;;) {
    const job = await getJob(id);
    onUpdate?.(job);
    if (TERMINAL_JOB_STATUSES.has(job.status)) return job;
    if (Date.now() - start > timeoutMs) {
      throw new Error('การวิเคราะห์ใช้เวลานานเกินไป (timeout)');
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
