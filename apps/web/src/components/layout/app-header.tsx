import { BrandMark } from '../brand/brand-mark';

export interface AppHeaderProps {
  tone?: 'paper' | 'transparent';
}

// The labels are the section headings, verbatim, in the order the page runs.
// They used to read Technology / Method / Evidence, which named nothing a
// visitor could find once the sections were renamed to the questions they
// answer - a menu whose words do not appear at the destination is a menu that
// has to be guessed at.
const navigation = [
  { href: '/#how', label: 'วิธีทำงาน' },
  { href: '/#tech', label: 'ตรวจสอบโมเดล' },
  { href: '/#proof', label: 'ความแม่นยำ' },
  { href: '/dashboard/viewer', label: 'ทดลองอัปโหลดไฟล์' },
  { href: '/demo', label: 'ดูตัวอย่างผลการประเมิน' },
  { href: '/login', label: 'เข้าสู่ระบบ' },
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
