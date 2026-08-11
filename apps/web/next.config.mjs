import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

/**
 * Content-Security-Policy.
 *
 * There was none. The other four headers here restrict framing, sniffing and
 * referrers, none of which say anything about where the page may load code from
 * or send data to.
 *
 * Every directive below was verified against the built site with the browser
 * console open — see apps/web/e2e/csp.spec.ts, which fails on any violation.
 * A CSP that has only been reasoned about is a header, not a control.
 *
 * `connect-src` is the one that carries product decisions. The browser talks to
 * whichever backend `resolveBackend()` picks, and that is deliberately not
 * fixed at build time (see the note in src/lib/api.ts): a quick tunnel gets a
 * new hostname on every start, so the runtime handoff wins over the baked-in
 * URL. The set here mirrors exactly what that handoff already validates —
 * a trycloudflare host or 127.0.0.1:8000 — plus Supabase for auth and whatever
 * NEXT_PUBLIC_API_URL was built with.
 */
function buildContentSecurityPolicy() {
  const connect = new Set(["'self'"]);

  for (const url of [process.env.NEXT_PUBLIC_API_URL, process.env.NEXT_PUBLIC_SUPABASE_URL]) {
    if (!url) continue;
    try {
      connect.add(new URL(url).origin);
    } catch {
      // A malformed value must not silently widen the policy, and must not
      // fail the build either — the app already treats an unusable API URL as
      // "not configured".
    }
  }

  // The demo handoff, whose hostname is not known until the launcher starts.
  connect.add('https://*.trycloudflare.com');
  connect.add('http://127.0.0.1:8000');
  connect.add('http://localhost:8000');
  // Supabase auth when the project URL is supplied at runtime rather than build
  // time, plus its realtime socket.
  connect.add('https://*.supabase.co');
  connect.add('wss://*.supabase.co');

  return [
    "default-src 'self'",
    // 'unsafe-inline' is required, not preferred. The App Router serves the
    // RSC payload and its bootstrap in inline <script> tags, and the only way
    // to drop it is a per-request nonce from middleware, which opts every page
    // out of static rendering. That trade is not worth making for a site whose
    // pages are static marketing and a client-side viewer; what this directive
    // still buys is that no THIRD-PARTY origin can serve script here.
    "script-src 'self' 'unsafe-inline'",
    // next/font and the Geist package inject <style> elements.
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self' data:",
    // blob: is the 3D viewer taking canvas snapshots; the remote hosts match
    // the images.remotePatterns above.
    "img-src 'self' data: blob: https://*.supabase.co https://images.unsplash.com",
    `connect-src ${[...connect].join(' ')}`,
    // Three.js loaders instantiate workers from blob URLs.
    "worker-src 'self' blob:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'self'",
    'upgrade-insecure-requests',
  ].join('; ');
}

const contentSecurityPolicy = buildContentSecurityPolicy();

/** @type {import('next').NextConfig} */
const nextConfig = {
  // No `output: 'standalone'`. Standalone tracing symlinks node_modules, which
  // needs Administrator rights or Developer Mode on Windows, so `next build`
  // fails on the team's own laptops. It also links into whichever pnpm store
  // resolved at build time, including git worktrees, so the bundle breaks when
  // that worktree is removed. The demo launcher serves the normal build with
  // `next start`, which needs neither.
  reactStrictMode: true,
  swcMinify: true,
  poweredByHeader: false,

  // Image optimization for Supabase Storage and external assets
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.supabase.co',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
  },

  // Transpile workspace packages
  transpilePackages: ['@carbonscan/ui', '@carbonscan/types', '@carbonscan/design-tokens'],

  // Experimental features
  experimental: {
    serverActions: {
      bodySizeLimit: '100mb', // for large LAS file uploads
    },
  },

  // Webpack config for 3D libraries
  webpack: (config) => {
    config.module.rules.push({
      test: /\.(glsl|vs|fs|vert|frag)$/,
      exclude: /node_modules/,
      use: ['raw-loader', 'glslify-loader'],
    });
    return config;
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'origin-when-cross-origin' },
          { key: 'Content-Security-Policy', value: contentSecurityPolicy },
        ],
      },
      {
        source: '/demo/:path*',
        headers: [
          { key: 'Referrer-Policy', value: 'no-referrer' },
          { key: 'Cache-Control', value: 'no-store' },
          { key: 'X-Robots-Tag', value: 'noindex, nofollow' },
        ],
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);
