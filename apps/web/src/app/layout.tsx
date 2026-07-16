import type { Metadata, Viewport } from 'next';
import { Inter, Sarabun, Space_Grotesk, JetBrains_Mono, Pacifico } from 'next/font/google';
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

// Script accent for the marketing hero (nature-landing feel).
const pacifico = Pacifico({
  subsets: ['latin'],
  weight: '400',
  variable: '--font-pacifico',
  display: 'swap',
});

// Metadata
export const metadata: Metadata = {
  title: {
    default: 'TreeQ Carbon Platform — Tree Biomass Carbon Assessment',
    template: '%s | TreeQ Carbon Platform',
  },
  description:
    'แพลตฟอร์มประเมินชีวมวล คาร์บอน และ CO₂e จาก 3D point cloud พร้อมหลักฐานที่ตรวจสอบย้อนกลับได้ — NSC 2026',
  keywords: [
    'TreeQ Carbon Platform',
    'Carbon Stock Estimate',
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
  authors: [{ name: 'TreeQ Carbon Platform Team' }],
  creator: 'TreeQ Carbon Platform Team',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'https://treeqcarbon.vercel.app'),
  icons: {
    icon: '/logo.png',
    shortcut: '/logo.png',
    apple: '/logo.png',
  },
  openGraph: {
    title: 'TreeQ Carbon Platform — Tree Biomass Carbon Assessment',
    description: 'ประเมินคาร์บอนจากต้นไม้ด้วย pipeline ที่แสดง provenance และข้อจำกัด',
    url: '/',
    siteName: 'TreeQ Carbon Platform',
    locale: 'th_TH',
    type: 'website',
    images: [
      {
        url: '/logo.png',
        width: 1024,
        height: 1024,
        alt: 'TreeQ Carbon Platform — ประเมินคาร์บอนจากต้นไม้พร้อม provenance',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TreeQ Carbon Platform',
    description: 'ประเมินคาร์บอนจากต้นไม้ด้วย pipeline ที่แสดง provenance และข้อจำกัด',
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="th"
      className={cn(
        inter.variable,
        sarabun.variable,
        spaceGrotesk.variable,
        jetbrainsMono.variable,
        pacifico.variable,
        GeistSans.variable,
        'font-sans',
      )}
      suppressHydrationWarning
    >
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}
