import type { ReactNode } from 'react';

import { cn } from '../../lib/utils';

export interface EditorialSectionProps {
  title: string;
  eyebrow?: string;
  description?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function EditorialSection({ title, eyebrow, description, children, className }: EditorialSectionProps) {
  return (
    <section className={cn('py-12 sm:py-16', className)}>
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <header className="max-w-3xl">
          {eyebrow ? <p className="editorial-eyebrow">{eyebrow}</p> : null}
          <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight text-forest-ink sm:text-4xl">{title}</h2>
          {description ? <div className="mt-4 text-base leading-7 text-canopy">{description}</div> : null}
        </header>
        {children ? <div className="mt-8">{children}</div> : null}
      </div>
    </section>
  );
}
