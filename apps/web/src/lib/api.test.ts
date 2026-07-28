import { afterEach, describe, expect, it, vi } from "vitest";

import type { AnalyzeResponse } from "./api";
import { analyzePointCloud, getJob, pollJobUntilDone, submitAnalyzeJob } from "./api";

describe("analyze diagnostics contract", () => {
  const base = {
    metadata: { status: "ok" },
    trees: [],
  } as unknown as AnalyzeResponse;

  it("carries excluded segments and counts that reconcile", () => {
    const result: AnalyzeResponse = {
      ...base,
      summary: {
        total_trees: 2,
        total_carbon_kg: 123.45,
        total_co2eq_kg: 452.6,
        detected_trees: 4,
        measured_trees: 2,
        excluded_trees: 2,
      },
      diagnostics: {
        excluded_segments: [
          { tree_id: 3, stage: "wood_leaf", reason_code: "WOOD_EMPTY" },
          { tree_id: 4, stage: "qsm", reason_code: "QSM_INVALID" },
        ],
      },
    };

    expect(result.summary.detected_trees).toBe(
      (result.summary.measured_trees ?? 0) + (result.summary.excluded_trees ?? 0),
    );
    expect(result.diagnostics?.excluded_segments).toHaveLength(
      result.summary.excluded_trees ?? 0,
    );
  });

  it("distinguishes a pre-0.4.0 result from one with nothing excluded", () => {
    const legacy: AnalyzeResponse = {
      ...base,
      summary: { total_trees: 2, total_carbon_kg: 123.45, total_co2eq_kg: 452.6 },
    };
    const nothingExcluded: AnalyzeResponse = {
      ...base,
      summary: {
        total_trees: 2,
        total_carbon_kg: 123.45,
        total_co2eq_kg: 452.6,
        detected_trees: 2,
        measured_trees: 2,
        excluded_trees: 0,
      },
      diagnostics: { excluded_segments: [] },
    };

    // Absent must stay absent: rendering it as 0 would claim an old run
    // excluded nothing, which it never reported either way.
    expect(legacy.summary.excluded_trees ?? null).toBeNull();
    expect(legacy.diagnostics ?? null).toBeNull();
    expect(nothingExcluded.summary.excluded_trees).toBe(0);
    expect(nothingExcluded.diagnostics?.excluded_segments).toEqual([]);
  });
});

describe("analyzePointCloud", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the file as multipart FormData to /api/v1/upload/analyze", async () => {
    const fakeResult = {
      metadata: { status: "ok" },
      summary: { total_trees: 2, total_carbon_kg: 123.45, total_co2eq_kg: 452.6 },
      trees: [],
    };
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => fakeResult,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const file = new File([new Uint8Array([1, 2, 3])], "plot.ply");
    const result = await analyzePointCloud(file);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [URL, RequestInit];
    expect(String(url)).toContain("/api/v1/upload/analyze");
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
    expect(result.summary.total_trees).toBe(2);
  });

  it("throws ApiError on a non-ok response", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: async () => ({ detail: "bad extension" }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const file = new File([new Uint8Array([1])], "photo.jpg");
    await expect(analyzePointCloud(file)).rejects.toThrowError(/API Error 400/);
  });
});

describe("async job API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submitAnalyzeJob POSTs FormData to /api/v1/jobs/analyze", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 202,
      json: async () => ({ id: "j1", status: "queued", created_at: "2026-01-01T00:00:00Z" }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const file = new File([new Uint8Array([1, 2, 3])], "plot.las");
    const res = await submitAnalyzeJob(file);

    const [url, init] = fetchMock.mock.calls[0] as unknown as [URL, RequestInit];
    expect(String(url)).toContain("/api/v1/jobs/analyze");
    expect(init.method).toBe("POST");
    expect(res.id).toBe("j1");
    expect(res.status).toBe("queued");
  });

  it("getJob GETs /api/v1/jobs/{id}", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ id: "j1", status: "completed", progress: 100, result: null }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const job = await getJob("j1");
    const [url] = fetchMock.mock.calls[0] as unknown as [URL];
    expect(String(url)).toContain("/api/v1/jobs/j1");
    expect(job.status).toBe("completed");
  });

  it("pollJobUntilDone returns immediately when the job is already terminal", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ id: "j1", status: "completed", progress: 100, result: null }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const job = await pollJobUntilDone("j1", { intervalMs: 1 });
    expect(job.status).toBe("completed");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
