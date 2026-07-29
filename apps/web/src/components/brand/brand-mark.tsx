import { cn } from '../../lib/utils';

export interface BrandMarkProps {
  className?: string;
}

export function BrandMark({ className }: BrandMarkProps) {
  return (
    <a href="/" aria-label="TreeQ Carbon home" className={cn('focus-ring inline-flex items-center gap-2 rounded-md', className)}>
      <svg aria-hidden="true" className="h-8 w-8 text-moss" viewBox="0 0 32 32" fill="none">
        <path d="M25.7 5.2C15.4 5.7 8.3 10.6 7.1 19.9c-.4 3.1.5 5.5 1.6 7 1.3-5.1 4.4-9.8 9.6-13.3-3.6 3.5-6 7.3-7.1 11.6 5.5 1 10.4-1.2 13-5.5 2.5-4.1 2.3-9.2 1.5-14.5Z" fill="currentColor" />
        <path d="M8.7 26.9c3-3.3 6.2-5.8 9.6-7.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <span className="font-display text-lg font-semibold tracking-tight text-forest-ink">TreeQ Carbon</span>
    </a>
  );
}
