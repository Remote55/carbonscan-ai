import { BrandMark } from '../brand/brand-mark';

export interface AppHeaderProps {
  tone?: 'paper' | 'transparent';
}

const navigation = [
  { href: '/#problem', label: 'ข้อจำกัดของการสำรวจแบบเดิม' },
  { href: '/#objectives', label: 'เป้าหมายโครงการ' },
  { href: '/#how', label: 'วิธีทำงาน' },
  { href: '/#tech', label: 'ชุดข้อมูล' },
  { href: '/#proof', label: 'ความแม่นยำ' },
  { href: '/login', label: 'เข้าสู่ระบบ' },
];

export function AppHeader({ tone = 'paper' }: AppHeaderProps) {
  const toneClass =
    tone === 'paper'
      ? 'border-b border-hairline bg-paper/90 shadow-sm backdrop-blur-xl'
      : 'border-b border-paper/10 bg-paper/80 backdrop-blur-xl';

  return (
    <header
      data-tone={tone}
      className={`fixed inset-x-0 top-0 z-50 w-full ${toneClass}`}
    >
      <div className="mx-auto flex min-h-16 max-w-7xl items-center justify-between gap-6 px-5 sm:px-8">
        <BrandMark />

        <nav
          aria-label="Primary navigation"
          className="hidden items-center gap-1 lg:flex"
        >
          {navigation.map((item) => {
            const isLogin = item.href === '/login';

            return (
              <a
                key={item.href}
                href={item.href}
                className={
                  isLogin
                    ? 'focus-ring rounded-full border border-moss/30 px-4 py-2 text-sm font-medium text-forest-ink transition-colors hover:bg-moss/10'
                    : 'focus-ring rounded-md px-3 py-2 text-sm font-medium text-canopy transition-colors hover:bg-moss/5 hover:text-deep-forest'
                }
              >
                {item.label}
              </a>
            );
          })}
        </nav>

        <details className="relative lg:hidden">
          <summary className="focus-ring cursor-pointer list-none rounded-full border border-hairline bg-paper px-4 py-2 text-sm font-medium text-forest-ink">
            เมนู
          </summary>

          <nav
              aria-label="Primary navigation mobile"
              className="absolute right-0 top-12 z-50 flex min-w-56 flex-col gap-1 rounded-2xl border border-hairline bg-paper p-2 shadow-xl"

          >
            {navigation.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="focus-ring rounded-xl px-4 py-3 text-sm font-medium text-canopy transition-colors hover:bg-gallery-ivory hover:text-deep-forest"
              >
                {item.label}
              </a>
            ))}
          </nav>
        </details>
      </div>
    </header>
  );
}