import { JUDGE_DEMO_EVIDENCE } from '../generated/judge-demo-evidence';

export interface FrozenDemoArtifactIdentity {
  path: string;
  sha256: string;
  size_bytes: number;
}

export interface FrozenDemoManifest {
  schema_version: number;
  analyzed_commit: string;
  git_dirty: boolean;
  artifacts: {
    input: FrozenDemoArtifactIdentity;
    result: FrozenDemoArtifactIdentity;
    segmented: FrozenDemoArtifactIdentity;
  };
  pipeline: {
    backend: string;
    species: string;
    version: string;
  };
  release: {
    status: string;
  };
}

export interface FrozenDemoTreeResult {
  tree_id: number;
  dbh_cm: number;
  height_m: number;
  carbon_kg: number;
  co2eq_kg: number;
}

export interface FrozenDemoResult {
  metadata: {
    algorithms: {
      species: string;
      wood_leaf: string;
    };
    git_commit: string;
    git_dirty: boolean;
    pipeline_version: string;
    status: string;
    wood_leaf_backend: string;
  };
  summary: {
    total_carbon_kg: number;
    total_co2eq_kg: number;
    total_trees: number;
    // Present once the bundle is regenerated with pipeline 0.4.0. Optional so a
    // bundle frozen by 0.3.0 still loads, and absent stays absent rather than 0.
    detected_trees?: number | null;
    measured_trees?: number | null;
    excluded_trees?: number | null;
  };
  diagnostics?: {
    excluded_segments?: Array<{
      tree_id: number;
      stage: 'wood_leaf' | 'qsm';
      reason_code: 'WOOD_EMPTY' | 'QSM_INVALID' | 'QSM_LOW_FIT_QUALITY';
    }>;
  } | null;
  trees: FrozenDemoTreeResult[];
}

export interface FrozenDemoBundle {
  mode: 'frozen';
  manifest: FrozenDemoManifest;
  result: FrozenDemoResult;
  input: Uint8Array;
  segmented: Uint8Array;
}

export interface FrozenDemoResponse {
  ok: boolean;
  status: number;
  arrayBuffer(): Promise<ArrayBuffer>;
}

export type FrozenDemoFetcher = (resource: string | URL) => Promise<FrozenDemoResponse>;

const SHA256 = /^[0-9a-f]{64}$/i;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function parseArtifact(value: unknown, expectedPath: string): FrozenDemoArtifactIdentity {
  if (
    !isRecord(value) ||
    value.path !== expectedPath ||
    typeof value.sha256 !== 'string' ||
    !SHA256.test(value.sha256) ||
    typeof value.size_bytes !== 'number' ||
    !Number.isSafeInteger(value.size_bytes) ||
    value.size_bytes < 0
  ) {
    throw new Error('Frozen demo manifest is invalid');
  }
  return {
    path: value.path,
    sha256: value.sha256.toLowerCase(),
    size_bytes: value.size_bytes,
  };
}

function parseManifest(value: unknown): FrozenDemoManifest {
  if (
    !isRecord(value) ||
    value.schema_version !== 1 ||
    typeof value.analyzed_commit !== 'string' ||
    !/^[0-9a-f]{40}$/i.test(value.analyzed_commit) ||
    typeof value.git_dirty !== 'boolean' ||
    !isRecord(value.artifacts) ||
    !isRecord(value.pipeline) ||
    typeof value.pipeline.backend !== 'string' ||
    typeof value.pipeline.species !== 'string' ||
    typeof value.pipeline.version !== 'string' ||
    !isRecord(value.release) ||
    typeof value.release.status !== 'string'
  ) {
    throw new Error('Frozen demo manifest is invalid');
  }

  return {
    schema_version: value.schema_version,
    analyzed_commit: value.analyzed_commit,
    git_dirty: value.git_dirty,
    artifacts: {
      input: parseArtifact(value.artifacts.input, JUDGE_DEMO_EVIDENCE.inputPath),
      result: parseArtifact(value.artifacts.result, JUDGE_DEMO_EVIDENCE.resultPath),
      segmented: parseArtifact(value.artifacts.segmented, JUDGE_DEMO_EVIDENCE.segmentedPath),
    },
    pipeline: {
      backend: value.pipeline.backend,
      species: value.pipeline.species,
      version: value.pipeline.version,
    },
    release: { status: value.release.status },
  };
}

function parseOptionalCount(
  summary: Record<string, unknown>,
  field: 'detected_trees' | 'measured_trees' | 'excluded_trees',
): number | undefined {
  if (!(field in summary)) return undefined;
  const count = summary[field];
  if (typeof count !== 'number' || !Number.isSafeInteger(count) || count < 0) {
    throw new Error('Frozen demo result is invalid');
  }
  return count;
}

function isExcludedStage(value: unknown): value is 'wood_leaf' | 'qsm' {
  return value === 'wood_leaf' || value === 'qsm';
}

function isExcludedReason(
  value: unknown,
): value is 'WOOD_EMPTY' | 'QSM_INVALID' | 'QSM_LOW_FIT_QUALITY' {
  return (
    value === 'WOOD_EMPTY' ||
    value === 'QSM_INVALID' ||
    value === 'QSM_LOW_FIT_QUALITY'
  );
}

function parseDiagnostics(value: unknown): NonNullable<FrozenDemoResult['diagnostics']> | undefined {
  if (value === undefined) return undefined;
  if (!isRecord(value) || !Array.isArray(value.excluded_segments)) {
    throw new Error('Frozen demo result is invalid');
  }

  const excludedTreeIds = new Set<number>();
  return {
    excluded_segments: value.excluded_segments.map((segment) => {
      if (
        !isRecord(segment) ||
        typeof segment.tree_id !== 'number' ||
        !Number.isSafeInteger(segment.tree_id) ||
        segment.tree_id < 0 ||
        !isExcludedStage(segment.stage) ||
        !isExcludedReason(segment.reason_code) ||
        !(
          (segment.stage === 'wood_leaf' && segment.reason_code === 'WOOD_EMPTY') ||
          (segment.stage === 'qsm' &&
            (segment.reason_code === 'QSM_INVALID' ||
              segment.reason_code === 'QSM_LOW_FIT_QUALITY'))
        ) ||
        excludedTreeIds.has(segment.tree_id)
      ) {
        throw new Error('Frozen demo result is invalid');
      }
      excludedTreeIds.add(segment.tree_id);
      return {
        tree_id: segment.tree_id,
        stage: segment.stage,
        reason_code: segment.reason_code,
      };
    }),
  };
}

function parseResult(value: unknown): FrozenDemoResult {
  if (
    !isRecord(value) ||
    !isRecord(value.metadata) ||
    !isRecord(value.metadata.algorithms) ||
    typeof value.metadata.algorithms.species !== 'string' ||
    typeof value.metadata.algorithms.wood_leaf !== 'string' ||
    typeof value.metadata.git_commit !== 'string' ||
    typeof value.metadata.git_dirty !== 'boolean' ||
    typeof value.metadata.pipeline_version !== 'string' ||
    typeof value.metadata.status !== 'string' ||
    typeof value.metadata.wood_leaf_backend !== 'string' ||
    !isRecord(value.summary) ||
    typeof value.summary.total_carbon_kg !== 'number' ||
    typeof value.summary.total_co2eq_kg !== 'number' ||
    typeof value.summary.total_trees !== 'number' ||
    !Array.isArray(value.trees)
  ) {
    throw new Error('Frozen demo result is invalid');
  }

  const trees = value.trees.map((tree) => {
    if (
      !isRecord(tree) ||
      typeof tree.tree_id !== 'number' ||
      typeof tree.dbh_cm !== 'number' ||
      typeof tree.height_m !== 'number' ||
      typeof tree.carbon_kg !== 'number' ||
      typeof tree.co2eq_kg !== 'number'
    ) {
      throw new Error('Frozen demo result is invalid');
    }
    return {
      tree_id: tree.tree_id,
      dbh_cm: tree.dbh_cm,
      height_m: tree.height_m,
      carbon_kg: tree.carbon_kg,
      co2eq_kg: tree.co2eq_kg,
    };
  });
  const detectedTrees = parseOptionalCount(value.summary, 'detected_trees');
  const measuredTrees = parseOptionalCount(value.summary, 'measured_trees');
  const excludedTrees = parseOptionalCount(value.summary, 'excluded_trees');
  const diagnostics = parseDiagnostics(value.diagnostics);
  const hasAnyModernField =
    detectedTrees !== undefined ||
    measuredTrees !== undefined ||
    excludedTrees !== undefined ||
    diagnostics !== undefined;

  if (hasAnyModernField) {
    if (
      detectedTrees === undefined ||
      measuredTrees === undefined ||
      excludedTrees === undefined ||
      diagnostics === undefined ||
      diagnostics.excluded_segments === undefined ||
      detectedTrees !== measuredTrees + excludedTrees ||
      measuredTrees !== value.summary.total_trees ||
      measuredTrees !== trees.length ||
      excludedTrees !== diagnostics.excluded_segments.length
    ) {
      throw new Error('Frozen demo result is invalid');
    }

    const measuredTreeIds = new Set(trees.map((tree) => tree.tree_id));
    if (diagnostics.excluded_segments.some((segment) => measuredTreeIds.has(segment.tree_id))) {
      throw new Error('Frozen demo result is invalid');
    }
  }

  return {
    metadata: {
      algorithms: {
        species: value.metadata.algorithms.species,
        wood_leaf: value.metadata.algorithms.wood_leaf,
      },
      git_commit: value.metadata.git_commit,
      git_dirty: value.metadata.git_dirty,
      pipeline_version: value.metadata.pipeline_version,
      status: value.metadata.status,
      wood_leaf_backend: value.metadata.wood_leaf_backend,
    },
    summary: {
      total_carbon_kg: value.summary.total_carbon_kg,
      total_co2eq_kg: value.summary.total_co2eq_kg,
      total_trees: value.summary.total_trees,
      ...(detectedTrees === undefined ? {} : { detected_trees: detectedTrees }),
      ...(measuredTrees === undefined ? {} : { measured_trees: measuredTrees }),
      ...(excludedTrees === undefined ? {} : { excluded_trees: excludedTrees }),
    },
    ...(diagnostics === undefined ? {} : { diagnostics }),
    trees,
  };
}

function copyToArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  return copy.buffer;
}

async function sha256(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', copyToArrayBuffer(bytes));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

async function fetchBytes(fetcher: FrozenDemoFetcher, resourcePath: string): Promise<Uint8Array> {
  const response = await fetcher(resourcePath);
  if (!response.ok) throw new Error(`Frozen demo loading failed (${response.status})`);
  return new Uint8Array(await response.arrayBuffer());
}

async function verifyBytes(
  label: string,
  bytes: Uint8Array,
  identity: FrozenDemoArtifactIdentity,
): Promise<void> {
  if (bytes.byteLength !== identity.size_bytes || (await sha256(bytes)) !== identity.sha256) {
    throw new Error(`Frozen demo ${label} hash mismatch`);
  }
}

const browserFetcher: FrozenDemoFetcher = (resource) => fetch(resource);

export async function loadFrozenDemo(
  fetcher: FrozenDemoFetcher = browserFetcher,
  expectedManifestSha256: string = JUDGE_DEMO_EVIDENCE.manifestSha256,
): Promise<FrozenDemoBundle> {
  if (!SHA256.test(expectedManifestSha256)) {
    throw new Error('Frozen demo expected manifest hash is invalid');
  }

  const manifestBytes = await fetchBytes(fetcher, JUDGE_DEMO_EVIDENCE.manifestPath);
  if ((await sha256(manifestBytes)) !== expectedManifestSha256.toLowerCase()) {
    throw new Error('Frozen demo manifest hash mismatch');
  }

  let manifestValue: unknown;
  try {
    manifestValue = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(manifestBytes));
  } catch {
    throw new Error('Frozen demo manifest is invalid');
  }
  const manifest = parseManifest(manifestValue);

  const [resultBytes, input, segmented] = await Promise.all([
    fetchBytes(fetcher, manifest.artifacts.result.path),
    fetchBytes(fetcher, manifest.artifacts.input.path),
    fetchBytes(fetcher, manifest.artifacts.segmented.path),
  ]);
  await Promise.all([
    verifyBytes('result', resultBytes, manifest.artifacts.result),
    verifyBytes('input', input, manifest.artifacts.input),
    verifyBytes('segmented', segmented, manifest.artifacts.segmented),
  ]);

  let resultValue: unknown;
  try {
    resultValue = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(resultBytes));
  } catch {
    throw new Error('Frozen demo result is invalid');
  }

  return {
    mode: 'frozen',
    manifest,
    result: parseResult(resultValue),
    input,
    segmented,
  };
}
