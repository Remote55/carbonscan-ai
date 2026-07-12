/**
 * API client for CarbonScan AI Backend (FastAPI).
 *
 * Uses native fetch with type-safe wrappers.
 * Auth token automatically attached if present in localStorage.
 */

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

  // Attach auth token if present
  const headers = new Headers(init.headers);
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) headers.set('Authorization', `Bearer ${token}`);
  }

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
