type VisualRights = 'team-owned' | 'generated' | 'CC0' | 'explicit-license';

export const VISUAL_ASSETS = {
  landing: { src: '/visual/forest-observatory/landing-mist.webp', rights: 'generated' },
  judge: { src: '/visual/forest-observatory/judge-road.webp', rights: 'generated' },
  auth: { src: '/visual/forest-observatory/auth-lake.webp', rights: 'generated' },
  dashboard: { src: '/visual/forest-observatory/dashboard-road.webp', rights: 'generated' },
} as const satisfies Record<string, { src: string; rights: VisualRights }>;
