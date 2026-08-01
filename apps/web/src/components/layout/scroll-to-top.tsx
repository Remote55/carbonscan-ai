'use client';

import { useEffect, useState } from 'react';

/**
 * Back to the top of a long page.
 *
 * The demo and viewer pages run several screens deep, and the mode badge,
 * the upload control and the reset button all live at the top - so reading
 * the results means scrolling back up by hand every time. A reviewer hit
 * that repeatedly before asking for this.
 *
 * Hidden until there is something to scroll back from, so it never covers
 * content on a page that fits.
 */
export function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 600);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  if (!visible) return null;

  return (
    <button
      type="button"
      // Respecting reduced motion is the caller's job nowhere else here, so it
      // is done at the call: an instant jump for anyone who asked for less
      // movement, a smooth one otherwise.
      onClick={() =>
        window.scrollTo({
          top: 0,
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 'auto'
            : 'smooth',
        })
      }
      aria-label="กลับขึ้นด้านบน"
      className="focus-ring fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full border border-moss bg-deep-forest text-paper shadow-[0_10px_28px_-8px_rgba(14,42,29,0.55)] transition-transform hover:-translate-y-0.5"
    >
      <svg
        viewBox="0 0 24 24"
        aria-hidden="true"
        className="h-5 w-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 19V5" />
        <path d="M5 12l7-7 7 7" />
      </svg>
    </button>
  );
}
