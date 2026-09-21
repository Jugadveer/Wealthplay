/**
 * Tailwind maps 1:1 onto the CSS custom properties in index.css.
 *
 * Colours are declared as `rgb(var(--x) / <alpha-value>)` so every Tailwind
 * opacity modifier (`bg-accent/10`) keeps working while the underlying value
 * still switches with the theme. There is one source of truth for colour, and
 * it is index.css — no component should ever contain a hex value.
 */
export default {
  darkMode: ['class', '[data-theme="dark"]'],
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: 'rgb(var(--paper) / <alpha-value>)',
          raised: 'rgb(var(--paper-raised) / <alpha-value>)',
          sunken: 'rgb(var(--paper-sunken) / <alpha-value>)',
        },
        ink: {
          DEFAULT: 'rgb(var(--ink) / <alpha-value>)',
          muted: 'rgb(var(--ink-muted) / <alpha-value>)',
          faint: 'rgb(var(--ink-faint) / <alpha-value>)',
        },
        rule: {
          DEFAULT: 'rgb(var(--rule) / <alpha-value>)',
          strong: 'rgb(var(--rule-strong) / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'rgb(var(--accent) / <alpha-value>)',
          hover: 'rgb(var(--accent-hover) / <alpha-value>)',
          on: 'rgb(var(--on-accent) / <alpha-value>)',
        },
        play: 'rgb(var(--play) / <alpha-value>)',
        up: 'rgb(var(--up) / <alpha-value>)',
        down: 'rgb(var(--down) / <alpha-value>)',
      },
      fontFamily: {
        display: ['"Instrument Serif"', 'Georgia', 'serif'],
        sans: ['Geist', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"Geist Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        // Editorial scale: small text stays small, display text gets genuinely
        // large. The gap between them is the hierarchy.
        micro: ['10px', { lineHeight: '1.4', letterSpacing: '0.14em' }],
        display: ['clamp(2.6rem, 6vw, 4.5rem)', { lineHeight: '1.02', letterSpacing: '-0.025em' }],
        headline: ['clamp(1.75rem, 3.4vw, 2.6rem)', { lineHeight: '1.08', letterSpacing: '-0.02em' }],
        title: ['1.3rem', { lineHeight: '1.2', letterSpacing: '-0.015em' }],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        DEFAULT: 'var(--radius)',
        lg: 'var(--radius-lg)',
      },
      boxShadow: {
        raise: 'var(--shadow-raise)',
        float: 'var(--shadow-float)',
      },
      maxWidth: {
        page: '1200px',
        wide: '1400px',
      },
      spacing: {
        header: 'var(--header-h)',
      },
      transitionTimingFunction: {
        out: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
}
