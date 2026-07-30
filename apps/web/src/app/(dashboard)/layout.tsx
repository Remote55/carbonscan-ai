import Link from 'next/link';
import { type ReactNode } from 'react';

import { SignOutButton } from '../../components/auth/sign-out-button';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="bg-background/80 sticky top-0 z-50 border-b border-border backdrop-blur-md">
        <nav className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="TreeQ Carbon" className="h-8 w-8 object-contain" />
            <span className="font-display text-base font-bold tracking-tight">TreeQ Carbon</span>
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
            <SignOutButton />
          </div>
        </nav>
      </header>
      {children}
    </div>
  );
}
