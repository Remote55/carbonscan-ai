import { afterEach, describe, expect, it, vi } from "vitest";

import { analyzePointCloud } from "./api";

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
