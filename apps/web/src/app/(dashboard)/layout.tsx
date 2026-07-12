import Link from 'next/link';
import { type ReactNode } from 'react';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <nav className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="CarbonScan AI" className="h-8 w-8 object-contain" />
            <span className="font-display text-base font-bold tracking-tight">CarbonScan AI</span>
          </Link>
          <div className="flex items-center gap-4 text-sm font-medium">
            <Link
              href="/dashboard"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/viewer"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              3D Viewer
            </Link>
          </div>
        </nav>
      </header>
      {children}
    </div>
  );
}
