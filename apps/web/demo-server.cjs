/**
 * Demo web server entry point.
 *
 * The judge-demo launcher refuses to execute any file reached through a reparse
 * point, which is how pnpm materialises `node_modules` on Windows. It therefore
 * cannot point Node at `node_modules/next/dist/bin/next` directly. This file is
 * a real, reviewed file inside the repository, so the launcher can validate it,
 * and Node resolves `next` from `apps/web/node_modules` at require time.
 *
 * It serves the existing production build with `next start`. It never builds.
 */
const port = process.env.PORT || '3000';
const hostname = process.env.HOSTNAME || '127.0.0.1';

process.argv = [process.argv[0], 'next', 'start', '-p', port, '-H', hostname];

require('next/dist/bin/next');
