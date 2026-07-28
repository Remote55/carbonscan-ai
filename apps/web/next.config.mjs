import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

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
