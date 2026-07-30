import { defineConfig } from 'vitest/config';

/**
 * Without this file vitest fell back to esbuild's classic JSX transform, so a
 * component was only renderable in a test if it happened to `import React` -
 * something Next never requires, because it compiles with the automatic
 * runtime. The mismatch was invisible for as long as the only component tested
 * was one that had the import: the first test to render `TreeResultTable` died
 * with "React is not defined" in code that works perfectly in the browser.
 *
 * Pinning the runtime here means tests exercise components the same way
 * production compiles them, rather than each new component having to add an
 * import that exists solely to satisfy the test environment.
 */
export default defineConfig({
  esbuild: { jsx: 'automatic' },
  test: {
    // Vitest's default include matches `*.spec.ts`, which is exactly what the
    // Playwright journey file is called, so adding e2e/ made vitest try to run a
    // browser suite it has no runner for and the unit gate went red for a reason
    // that had nothing to do with the unit tests. The two suites are started by
    // different commands and must stay in separate pools.
    exclude: ['**/node_modules/**', '**/dist/**', '**/.next/**', 'e2e/**'],
  },
});
