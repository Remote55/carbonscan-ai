import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Tailwind class name merger.
 * Combines clsx (conditional classes) with tailwind-merge (deduplicates conflicting Tailwind classes).
 *
 * @example
 * cn('text-red-500', isActive && 'bg-blue-500', 'text-blue-500')
 * // → 'bg-blue-500 text-blue-500' (text-red-500 is overridden)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as carbon (kg or tonnes depending on magnitude).
 */
export function formatCarbon(kg: number): string {
  if (kg >= 1000) {
    return `${(kg / 1000).toFixed(2)} tCO₂eq`;
  }
  return `${kg.toFixed(1)} kgCO₂eq`;
}

/**
 * Format Thai Baht currency.
 */
export function formatTHB(amount: number): string {
  return new Intl.NumberFormat('th-TH', {
    style: 'currency',
    currency: 'THB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format date in Thai locale.
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('th-TH', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(d);
}

/**
 * Format GPS coordinates with 6-decimal precision (≈ 0.1m accuracy).
 */
export function formatGPS(lat: number, lon: number): string {
  return `${lat.toFixed(6)}°N, ${lon.toFixed(6)}°E`;
}

/**
 * Truncate string with ellipsis.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 1)}…`;
}

/**
 * Sleep helper for testing/throttling.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
