import { BrandMark } from '../brand/brand-mark';

export interface AppHeaderProps {
  tone?: 'paper' | 'transparent';
}

const navigation = [
  { href: '/#tech', label: 'Technology' },
  { href: '/#how', label: 'Method' },
  { href: '/#proof', label: 'Evidence' },
  { href: '/dashboard/viewer', label: 'Workspace' },
  { href: '/login', label: 'Sign in' },
  { href: '/demo', label: 'Demo' },
];

export function AppHeader({ tone = 'paper' }: AppHeaderProps) {
  const toneClass = tone === 'paper' ? 'border-b border-hairline bg-paper/95' : 'bg-transparent';

  return (
    <header data-tone={tone} className={toneClass}>
      <div className="mx-auto flex min-h-16 max-w-7xl items-center justify-between gap-6 px-5 sm:px-8">
        <BrandMark />
        <nav aria-label="Primary navigation" className="flex flex-wrap items-center justify-end gap-x-4 gap-y-2 text-sm">
          {navigation.map((item) => (
            <a key={item.href} href={item.href} className="focus-ring rounded-md text-canopy hover:text-deep-forest">
              {item.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
