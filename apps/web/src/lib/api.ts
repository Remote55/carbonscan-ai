/**
 * API client for TreeQ Carbon Platform Backend (FastAPI).
 *
 * Uses native fetch with type-safe wrappers.
 * Auth token automatically attached if present in localStorage.
 */

import { createClient } from './supabase';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

/**
 * True when a real backend API is configured (env var set to a non-localhost URL).
 * The deployed demo has no backend, so the carbon-analysis UI checks this to show
 * a clear message instead of a raw "Failed to fetch" network error.
 */
export const IS_API_CONFIGURED =
  typeof process.env.NEXT_PUBLIC_API_URL === 'string' &&
  process.env.NEXT_PUBLIC_API_URL.length > 0 &&
  !process.env.NEXT_PUBLIC_API_URL.includes('localhost');

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

  // Build URL with query params
  const url = new URL(`/api/v1${path}`, API_URL);
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

export interface AnalyzeSummary {
  total_trees: number;
  total_carbon_kg: number;
  total_co2eq_kg: number;
}

export interface AnalyzeResponse {
  metadata: Record<string, unknown>;
  summary: AnalyzeSummary;
  trees: AnalyzeTree[];
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
