import { beforeAll, describe, expect, it } from 'vitest';
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
