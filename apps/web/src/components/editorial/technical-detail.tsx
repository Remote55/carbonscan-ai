import type { ReactNode } from 'react';

/**
 * The technical reading of the section above it.
 *
 * Native <details> rather than a hand-built accordion: it gives a control that
 * responds to Enter and Space, announces its own open state to a screen
 * reader, and works before any JavaScript has loaded. Building the same thing
 * by hand means owning aria-expanded and focus for no gain.
 *
 * One label for the whole site, so a reader learns once where the jargon
 * lives instead of decoding a different phrase in every section.
 */
export function TechnicalDetail({ children }: { children: ReactNode }) {
  return (
    <details className="mt-4 rounded-xl border border-hairline bg-paper px-4 py-3">
      <summary className="cursor-pointer text-sm font-medium text-canopy marker:text-evidence-amber">
        รายละเอียดทางเทคนิค
      </summary>
      <div className="mt-3 text-sm leading-7 text-canopy">{children}</div>
    </details>
  );
}
