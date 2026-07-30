import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{ts,tsx}',
    './src/components/**/*.{ts,tsx}',
    './src/app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: '',
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
      },
      extend: {
      colors: {
        'forest-ink': 'var(--forest-ink)',
        'deep-forest': 'var(--deep-forest)',
        canopy: 'var(--canopy)',
        moss: 'var(--moss)',
        lichen: 'var(--lichen)',
        'gallery-ivory': 'var(--gallery-ivory)',
        paper: 'var(--paper)',
        mist: 'var(--mist)',
        'evidence-amber': 'var(--evidence-amber)',
        clay: 'var(--clay)',
        hairline: 'var(--hairline)',

        // Legacy aliases remain while existing surfaces migrate to semantic tokens.
        forest: {
          50: 'var(--paper)',
          100: 'var(--mist)',
          200: 'var(--lichen)',
          300: 'var(--lichen)',
          400: 'var(--moss)',
          500: 'var(--canopy)',
          600: 'var(--canopy)',
          700: 'var(--deep-forest)',
          800: 'var(--deep-forest)',
          900: 'var(--forest-ink)',
        },
        border: 'var(--border)',
        input: 'var(--input)',
        ring: 'var(--ring)',
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        primary: {
          DEFAULT: 'var(--primary)',
          foreground: 'var(--primary-foreground)',
        },
        secondary: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--secondary-foreground)',
        },
        destructive: {
          DEFAULT: 'var(--destructive)',
          foreground: 'var(--destructive-foreground)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-foreground)',
        },
        popover: {
          DEFAULT: 'var(--popover)',
          foreground: 'var(--popover-foreground)',
        },
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--card-foreground)',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      // The design spec puts hover and focus at 180-220ms. Tailwind's bare
      // `transition` and `transition-colors` default to 150ms, so every
      // interactive element was quicker than the system it is meant to follow -
      // including the editorial Button, whose `transition-all` carries no
      // duration of its own. Moving the DEFAULT means a component gets the right
      // timing from using a transition utility at all, rather than every call
      // site having to remember a `duration-*` class and one of them forgetting.
      //
      // The spec's second tier - 240-320ms for section and viewer transitions -
      // has no token here on purpose: nothing in the redesign animates a section
      // or the viewer, so a `duration-surface` would be config with no consumer.
      // Add it at 280ms alongside the first transition that needs it.
      transitionDuration: {
        DEFAULT: '200ms',
      },
      fontFamily: {
        sans: ['var(--font-ui)', 'system-ui', 'sans-serif'],
        heading: ['var(--font-editorial)', 'serif'],
        display: ['var(--font-editorial)', 'serif'],
        mono: ['var(--font-technical)', 'monospace'],
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.4s ease-out',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
