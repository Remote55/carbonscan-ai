import { describe, expect, it } from 'vitest';

import { formatBackendLabel, formatEvidenceStatus } from './evidence';

const metadata = {
  pipeline_version: '0.3.0',
  git_commit: '0036996',
  git_dirty: false,
  wood_leaf_backend: 'tlsep',
  input_sha256: 'a'.repeat(64),
  checkpoint_sha256: null,
  algorithms: { species: 'stub', wood_leaf: 'tlsep' },
  evidence_status: 'baseline',
  candidate_status: 'candidate_not_evaluated',
  n_input_points: 1000,
  status: 'ok',
};

describe('evidence labels', () => {
  it('labels tlsep as the baseline without calling it PointNet++', () => {
    expect(formatBackendLabel(metadata)).toBe('Baseline: tlsep');
  });

  it('states that the candidate was not evaluated', () => {
    expect(formatEvidenceStatus(metadata)).toContain('candidate not evaluated');
  });

  it('warns when the analyzed worktree was dirty', () => {
    expect(formatEvidenceStatus({ ...metadata, git_dirty: true })).toContain('uncommitted changes');
  });
});
