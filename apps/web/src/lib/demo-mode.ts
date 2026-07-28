import type { RuntimeCredentials } from './demo-runtime';

export type { RuntimeCredentials } from './demo-runtime';

export type DemoModeState =
  | { kind: 'booting' }
  | { kind: 'checking'; credentials: RuntimeCredentials }
  | { kind: 'production-live'; credentials: RuntimeCredentials; pipelineVersion: string }
  | { kind: 'local-live'; credentials: RuntimeCredentials; pipelineVersion: string }
  | { kind: 'frozen'; reason: 'sample-first' | 'invalid-handoff' | 'unreachable' | 'manual' };

export type DemoModeEvent =
  | { type: 'BOOT'; credentials: RuntimeCredentials | null; invalidHandoff: boolean }
  | { type: 'READINESS_OK'; pipelineVersion: string }
  | { type: 'READINESS_FAILED' }
  | { type: 'USE_FROZEN' };

export function demoModeReducer(state: DemoModeState, event: DemoModeEvent): DemoModeState {
  if (state.kind === 'booting' && event.type === 'BOOT') {
    if (event.credentials) return { kind: 'checking', credentials: event.credentials };
    return { kind: 'frozen', reason: event.invalidHandoff ? 'invalid-handoff' : 'sample-first' };
  }

  if (state.kind === 'checking') {
    if (event.type === 'READINESS_FAILED') return { kind: 'frozen', reason: 'unreachable' };
    if (event.type === 'USE_FROZEN') return { kind: 'frozen', reason: 'manual' };
    if (event.type === 'READINESS_OK') {
      return state.credentials.endpoint === 'http://127.0.0.1:8000'
        ? {
            kind: 'local-live',
            credentials: state.credentials,
            pipelineVersion: event.pipelineVersion,
          }
        : {
            kind: 'production-live',
            credentials: state.credentials,
            pipelineVersion: event.pipelineVersion,
          };
    }
  }

  if (
    (state.kind === 'production-live' || state.kind === 'local-live') &&
    event.type === 'USE_FROZEN'
  ) {
    return { kind: 'frozen', reason: 'manual' };
  }

  return state;
}
