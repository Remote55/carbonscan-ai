import { describe, expect, it } from 'vitest';

import { demoModeReducer, type DemoModeState, type RuntimeCredentials } from './demo-mode';

const tunnelCredentials: RuntimeCredentials = {
  endpoint: 'https://green-tree.trycloudflare.com',
  token: 'a'.repeat(64),
};

const localCredentials: RuntimeCredentials = {
  endpoint: 'http://127.0.0.1:8000',
  token: 'b'.repeat(64),
};

const localhostCredentials: RuntimeCredentials = {
  endpoint: 'http://localhost:8000',
  token: 'c'.repeat(64),
};

describe('demoModeReducer', () => {
  it('uses frozen sample-first mode when no handoff was supplied', () => {
    const state = demoModeReducer(
      { kind: 'booting' },
      {
        type: 'BOOT',
        credentials: null,
        invalidHandoff: false,
      },
    );

    expect(state).toEqual({ kind: 'frozen', reason: 'sample-first' });
  });

  it('records an invalid handoff instead of attempting readiness', () => {
    const state = demoModeReducer(
      { kind: 'booting' },
      {
        type: 'BOOT',
        credentials: null,
        invalidHandoff: true,
      },
    );

    expect(state).toEqual({ kind: 'frozen', reason: 'invalid-handoff' });
  });

  it('promotes verified tunnel readiness to production-live', () => {
    const checking = demoModeReducer(
      { kind: 'booting' },
      {
        type: 'BOOT',
        credentials: tunnelCredentials,
        invalidHandoff: false,
      },
    );
    const state = demoModeReducer(checking, { type: 'READINESS_OK', pipelineVersion: 'tlsep-v1' });

    expect(state).toEqual({
      kind: 'production-live',
      credentials: tunnelCredentials,
      pipelineVersion: 'tlsep-v1',
    });
  });

  it('promotes verified local readiness to local-live', () => {
    const checking = demoModeReducer(
      { kind: 'booting' },
      {
        type: 'BOOT',
        credentials: localCredentials,
        invalidHandoff: false,
      },
    );
    const state = demoModeReducer(checking, { type: 'READINESS_OK', pipelineVersion: 'tlsep-v1' });

    expect(state).toEqual({
      kind: 'local-live',
      credentials: localCredentials,
      pipelineVersion: 'tlsep-v1',
    });
  });

  it('promotes verified localhost readiness to local-live', () => {
    const checking = demoModeReducer(
      { kind: 'booting' },
      {
        type: 'BOOT',
        credentials: localhostCredentials,
        invalidHandoff: false,
      },
    );
    const state = demoModeReducer(checking, {
      type: 'READINESS_OK',
      pipelineVersion: 'tlsep-v1',
    });

    expect(state).toEqual({
      kind: 'local-live',
      credentials: localhostCredentials,
      pipelineVersion: 'tlsep-v1',
    });
  });

  it('freezes the demo with an unreachable reason after readiness fails', () => {
    const checking: DemoModeState = { kind: 'checking', credentials: tunnelCredentials };

    expect(demoModeReducer(checking, { type: 'READINESS_FAILED' })).toEqual({
      kind: 'frozen',
      reason: 'unreachable',
    });
  });

  it('never changes frozen mode to live without a verified checking state', () => {
    const frozen: DemoModeState = { kind: 'frozen', reason: 'manual' };

    expect(demoModeReducer(frozen, { type: 'READINESS_OK', pipelineVersion: 'forged' })).toEqual(
      frozen,
    );
  });
});
