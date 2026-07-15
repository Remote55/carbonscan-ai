import type { Metadata, Viewport } from 'next';
import {
  Inter,
  Sarabun,
  Space_Grotesk,
  JetBrains_Mono,
  Fraunces,
} from 'next/font/google';
import { GeistSans } from 'geist/font/sans';
import './globals.css';
import { cn } from '@/lib/utils';

// Fonts
const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const sarabun = Sarabun({
  subsets: ['thai', 'latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-sarabun',
  display: 'swap',
});

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

// Premium display serif for the marketing surface (hero + landing sections).
const fraunces = Fraunces({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-fraunces',
  display: 'swap',
});

// Metadata
export const metadata: Metadata = {
  title: {
    default: 'CarbonScan AI — Tree Biomass Carbon Assessment Platform',
    template: '%s | CarbonScan AI',
  },
  description:
    'แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ด้วย LiDAR Point Cloud + AI Wood-Leaf Segmentation + B2B Carbon Offset Matchmaking — NSC 2026',
  keywords: [
    'CarbonScan AI',
    'Carbon Credit',
    'LiDAR',
    'Point Cloud',
    'Deep Learning',
    'Tree Biomass',
    'Allometric Equation',
    'TGO',
    'NSC 2026',
    'Climate Tech',
    'Sustainable Innovation',
  ],
  authors: [{ name: 'CarbonScan AI Team' }],
  creator: 'CarbonScan AI Team',
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? 'https://carbonscan-ai.vercel.app',
  ),
  icons: {
    icon: '/logo.png',
    shortcut: '/logo.png',
    apple: '/logo.png',
  },
  openGraph: {
    title: 'CarbonScan AI — Tree Biomass Carbon Assessment',
    description: 'แปลงต้นไม้เป็น Carbon Credits ด้วย AI ที่โปร่งใส',
    url: '/',
    siteName: 'CarbonScan AI',
    locale: 'th_TH',
    type: 'website',
    images: [
      {
        url: '/logo.png',
        width: 1024,
        height: 1024,
        alt: 'CarbonScan AI — แปลงต้นไม้เป็น Carbon Credits',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CarbonScan AI',
    description: 'แปลงต้นไม้เป็น Carbon Credits ด้วย AI ที่โปร่งใส',
    images: ['/logo.png'],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FAFAF8' },
    { media: '(prefers-color-scheme: dark)', color: '#0F3324' },
  ],
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="th"
      className={cn(
        inter.variable,
        sarabun.variable,
        spaceGrotesk.variable,
        jetbrainsMono.variable,
        fraunces.variable,
        GeistSans.variable,
        'font-sans',
      )}
      suppressHydrationWarning
    >
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}
