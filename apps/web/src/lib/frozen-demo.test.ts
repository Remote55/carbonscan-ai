import { beforeAll, describe, expect, it } from 'vitest';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

import { JUDGE_DEMO_EVIDENCE } from '../generated/judge-demo-evidence';
import { loadFrozenDemo, type FrozenDemoFetcher } from './frozen-demo';

const ARTIFACT_PATHS = [
  JUDGE_DEMO_EVIDENCE.manifestPath,
  JUDGE_DEMO_EVIDENCE.inputPath,
  JUDGE_DEMO_EVIDENCE.segmentedPath,
  JUDGE_DEMO_EVIDENCE.resultPath,
] as const;

let validFiles: ReadonlyMap<string, Uint8Array>;

function copyToArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  return copy.buffer;
}

function fakeFetcher(files: ReadonlyMap<string, Uint8Array>): FrozenDemoFetcher {
  return async (resource) => {
    const resourcePath = typeof resource === 'string' ? resource : resource.pathname;
    const bytes = files.get(resourcePath);
    return bytes
      ? new Response(copyToArrayBuffer(bytes), { status: 200 })
      : new Response('not found', { status: 404 });
  };
}

function withChangedByte(
  files: ReadonlyMap<string, Uint8Array>,
  resourcePath: string,
): ReadonlyMap<string, Uint8Array> {
  const changedFiles = new Map(files);
  const original = files.get(resourcePath);
  if (!original) throw new Error(`Missing fixture: ${resourcePath}`);
  const changed = new Uint8Array(original);
  changed[changed.byteLength - 1] ^= 1;
  changedFiles.set(resourcePath, changed);
  return changedFiles;
}

function jsonBytes(value: unknown): Uint8Array {
  return new TextEncoder().encode(JSON.stringify(value));
}

function sha256(bytes: Uint8Array): string {
  return createHash('sha256').update(bytes).digest('hex');
}

async function withResultMutation(
  mutate: (result: Record<string, unknown>) => void,
): Promise<{ files: ReadonlyMap<string, Uint8Array>; manifestSha256: string }> {
  const resultBytes = validFiles.get(JUDGE_DEMO_EVIDENCE.resultPath);
  const manifestBytes = validFiles.get(JUDGE_DEMO_EVIDENCE.manifestPath);
  if (!resultBytes || !manifestBytes) throw new Error('Missing frozen test fixture');

  const result = JSON.parse(new TextDecoder().decode(resultBytes)) as Record<string, unknown>;
  mutate(result);
  const nextResultBytes = jsonBytes(result);

  const manifest = JSON.parse(new TextDecoder().decode(manifestBytes)) as {
    artifacts: { result: { sha256: string; size_bytes: number } };
  };
  manifest.artifacts.result.sha256 = sha256(nextResultBytes);
  manifest.artifacts.result.size_bytes = nextResultBytes.byteLength;
  const nextManifestBytes = jsonBytes(manifest);

  const files = new Map(validFiles);
  files.set(JUDGE_DEMO_EVIDENCE.resultPath, nextResultBytes);
  files.set(JUDGE_DEMO_EVIDENCE.manifestPath, nextManifestBytes);
  return { files, manifestSha256: sha256(nextManifestBytes) };
}

beforeAll(async () => {
  const publicRoot = path.resolve(process.cwd(), 'public');
  validFiles = new Map(
    await Promise.all(
      ARTIFACT_PATHS.map(
        async (resourcePath) =>
          [
            resourcePath,
            new Uint8Array(await readFile(path.join(publicRoot, resourcePath))),
          ] as const,
      ),
    ),
  );
});

describe('loadFrozenDemo', () => {
  it('loads only when the manifest and every artifact hash match', async () => {
    const bundle = await loadFrozenDemo(
      fakeFetcher(validFiles),
      JUDGE_DEMO_EVIDENCE.manifestSha256,
    );

    expect(bundle.mode).toBe('frozen');
    expect(bundle.result.metadata.wood_leaf_backend).toBe('tlsep');
  });

  it('preserves verified counts and diagnostics from the current frozen artifact', async () => {
    const bundle = await loadFrozenDemo(
      fakeFetcher(validFiles),
      JUDGE_DEMO_EVIDENCE.manifestSha256,
    );

    expect(bundle.result.summary).toMatchObject({
      detected_trees: 5,
      measured_trees: 3,
      excluded_trees: 2,
    });
    expect(bundle.result.diagnostics?.excluded_segments).toEqual([
      { tree_id: 1, stage: 'qsm', reason_code: 'QSM_INVALID' },
      { tree_id: 4, stage: 'qsm', reason_code: 'QSM_INVALID' },
    ]);
  });

  it('keeps optional counts and diagnostics absent for a verified legacy bundle', async () => {
    const fixture = await withResultMutation((result) => {
      const summary = result.summary as Record<string, unknown>;
      delete summary.detected_trees;
      delete summary.measured_trees;
      delete summary.excluded_trees;
      delete result.diagnostics;
    });

    const bundle = await loadFrozenDemo(
      fakeFetcher(fixture.files),
      fixture.manifestSha256,
    );
    expect(bundle.result.summary.detected_trees).toBeUndefined();
    expect(bundle.result.summary.measured_trees).toBeUndefined();
    expect(bundle.result.summary.excluded_trees).toBeUndefined();
    expect(bundle.result.diagnostics).toBeUndefined();
  });

  it.each([
    ['negative count', (result: Record<string, unknown>) => {
      (result.summary as Record<string, unknown>).detected_trees = -1;
    }],
    ['fractional count', (result: Record<string, unknown>) => {
      (result.summary as Record<string, unknown>).measured_trees = 2.5;
    }],
    ['unsafe count', (result: Record<string, unknown>) => {
      (result.summary as Record<string, unknown>).excluded_trees = Number.MAX_SAFE_INTEGER + 1;
    }],
    ['invalid diagnostics shape', (result: Record<string, unknown>) => {
      result.diagnostics = { excluded_segments: 'not-an-array' };
    }],
    ['invalid diagnostics stage', (result: Record<string, unknown>) => {
      const diagnostics = result.diagnostics as { excluded_segments: Array<Record<string, unknown>> };
      diagnostics.excluded_segments[0].stage = 'invented';
    }],
    ['invalid diagnostics reason code', (result: Record<string, unknown>) => {
      const diagnostics = result.diagnostics as { excluded_segments: Array<Record<string, unknown>> };
      diagnostics.excluded_segments[0].reason_code = 'UNKNOWN';
    }],
  ] as const)('fails closed on a verified result with %s', async (_label, mutate) => {
    const fixture = await withResultMutation(mutate);

    await expect(
      loadFrozenDemo(fakeFetcher(fixture.files), fixture.manifestSha256),
    ).rejects.toThrow('Frozen demo result is invalid');
  });

  it.each([
    ['manifest', JUDGE_DEMO_EVIDENCE.manifestPath],
    ['result', JUDGE_DEMO_EVIDENCE.resultPath],
    ['input', JUDGE_DEMO_EVIDENCE.inputPath],
    ['segmented', JUDGE_DEMO_EVIDENCE.segmentedPath],
  ])('fails closed on a changed %s byte', async (_artifact, resourcePath) => {
    await expect(
      loadFrozenDemo(
        fakeFetcher(withChangedByte(validFiles, resourcePath)),
        JUDGE_DEMO_EVIDENCE.manifestSha256,
      ),
    ).rejects.toThrow(/hash mismatch/i);
  });
});
