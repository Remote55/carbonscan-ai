import type { AnalyzeMetadata } from './api';

export function formatBackendLabel(metadata: AnalyzeMetadata): string {
  return metadata.wood_leaf_backend === 'tlsep'
    ? 'Baseline: tlsep'
    : `Experimental candidate: ${metadata.wood_leaf_backend}`;
}

export function formatEvidenceStatus(metadata: AnalyzeMetadata): string {
  if (metadata.git_dirty) {
    return 'Run provenance warning: uncommitted changes were present.';
  }
  if (metadata.candidate_status === 'candidate_not_evaluated') {
    return 'PointNet++ candidate not evaluated; tlsep result shown.';
  }
  if (metadata.evidence_status === 'experimental') {
    return 'Experimental result; not promoted to the default pipeline.';
  }
  return 'Baseline result with run provenance attached.';
}
