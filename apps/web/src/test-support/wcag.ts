/**
 * WCAG contrast helpers for tests, reading the real tokens out of globals.css.
 *
 * Asserting on class names is not enough. The table test used to check only that
 * the READY badge carried `text-canopy`, which said nothing about the ratio and
 * nothing at all about the EXCLUDED badge beside it - so `text-clay` on a Gallery
 * Ivory row sat at 4.28:1 through a review whose stated goal was AA compliance.
 *
 * These functions compute the ratio from the stylesheet, so a token edit that
 * breaks contrast fails a test instead of shipping.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

/** Reads a `--token: #rrggbb` declaration from the app stylesheet. */
export function tokenHex(token: string, css: string = readGlobalsCss()): string {
  const match = css.match(new RegExp(`--${token}:\\s*(#[0-9a-f]{6})`, 'i'));
  if (!match) throw new Error(`Missing color token: ${token}`);
  return match[1];
}

export function readGlobalsCss(): string {
  return readFileSync(path.resolve(process.cwd(), 'src/app/globals.css'), 'utf8');
}

function channels(hex: string): [number, number, number] {
  const parsed = hex
    .slice(1)
    .match(/.{2}/g)!
    .map((value) => parseInt(value, 16));
  return [parsed[0], parsed[1], parsed[2]];
}

export function relativeLuminance(hex: string): number {
  const linear = channels(hex)
    .map((value) => value / 255)
    .map((value) => (value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4)));
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

export function contrastRatio(foreground: string, background: string): number {
  const first = relativeLuminance(foreground);
  const second = relativeLuminance(background);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

/**
 * The colour a `bg-<token>/<alpha>` tint actually resolves to over an opaque
 * surface. Tailwind's slash opacity composites in sRGB, and the contrast of the
 * text above it depends on the composited result - not on either input - which is
 * why the upload error sat below AA while both of its tokens looked fine alone.
 */
export function compositeOver(foreground: string, background: string, alpha: number): string {
  const top = channels(foreground);
  const bottom = channels(background);
  const mixed = top.map((value, index) => Math.round(value * alpha + bottom[index] * (1 - alpha)));
  return `#${mixed.map((value) => value.toString(16).padStart(2, '0')).join('')}`;
}
