import { afterEach, describe, expect, it, vi } from "vitest";

import type { AnalyzeResponse } from "./api";
import { analyzePointCloud, isApiConfigured } from "./api";
import { RUNTIME_STORAGE_KEY } from "./demo-runtime";

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

describe("backend resolution", () => {
  const TUNNEL = "https://green-tree.trycloudflare.com";
  const TOKEN = "e".repeat(64);

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // These tests run in the node environment, like the rest of this file, so the
  // browser has to be supplied rather than assumed. Stubbing just the surface
  // the client touches keeps this file free of a jsdom dependency that nothing
  // else here needs.
  function stubBrowser(stored?: { endpoint: string; token: string }) {
    const values = new Map<string, string>();
    if (stored) values.set(RUNTIME_STORAGE_KEY, JSON.stringify(stored));
    vi.stubGlobal("window", {
      sessionStorage: { getItem: (key: string) => values.get(key) ?? null },
    });
  }

  function stubOkFetch() {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) }));
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
  }

  it("sends the request to the handed-off tunnel, not the built-in URL", async () => {
    // The whole point of the change: NEXT_PUBLIC_API_URL is fixed at build
    // time, and a quick tunnel is not. A request that ignored the handoff would
    // go to whichever tunnel happened to be alive on the day of the build.
    stubBrowser({ endpoint: TUNNEL, token: TOKEN });
    const fetchMock = stubOkFetch();

    await analyzePointCloud(new File([new Uint8Array([1])], "plot.ply"));

    const [url] = fetchMock.mock.calls[0] as unknown as [URL];
    expect(url.origin).toBe(TUNNEL);
  });

  it("carries the demo token, which the API's upload guard requires", async () => {
    stubBrowser({ endpoint: TUNNEL, token: TOKEN });
    const fetchMock = stubOkFetch();

    await analyzePointCloud(new File([new Uint8Array([1])], "plot.ply"));

    const [, init] = fetchMock.mock.calls[0] as unknown as [URL, RequestInit];
    expect(new Headers(init.headers).get("x-treeq-demo-token")).toBe(TOKEN);
  });

  it("sends no demo token when neither a handoff nor a built-in one exists", async () => {
    // NEXT_PUBLIC_DEMO_TOKEN is unset in this test environment, so nothing is
    // available to send. Inventing a header here would put a value on the wire
    // that this browser was never given.
    stubBrowser();
    const fetchMock = stubOkFetch();

    await analyzePointCloud(new File([new Uint8Array([1])], "plot.ply"));

    const [, init] = fetchMock.mock.calls[0] as unknown as [URL, RequestInit];
    expect(new Headers(init.headers).has("x-treeq-demo-token")).toBe(false);
  });

  it("reports itself configured once a handoff is stored", () => {
    stubBrowser();
    expect(isApiConfigured()).toBe(false);

    stubBrowser({ endpoint: TUNNEL, token: TOKEN });
    expect(isApiConfigured()).toBe(true);
  });

  it("ignores a stored endpoint that is not an allowed demo origin", async () => {
    stubBrowser({ endpoint: "https://attacker.test", token: TOKEN });
    const fetchMock = stubOkFetch();

    await analyzePointCloud(new File([new Uint8Array([1])], "plot.ply"));

    const [url, init] = fetchMock.mock.calls[0] as unknown as [URL, RequestInit];
    expect(url.origin).not.toBe("https://attacker.test");
    expect(new Headers(init.headers).has("x-treeq-demo-token")).toBe(false);
  });
});

