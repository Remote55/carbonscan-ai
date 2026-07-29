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
});
