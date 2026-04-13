
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          1: '#ff6b35',
          2: '#f59e0b',
          50: '#fff7ed',
          100: '#ffedd5',
          400: '#fb923c',
          500: '#ff6b35',
          600: '#ea580c',
          primary: '#ff6b35',
          primaryDark: '#ea580c',
        },
        authority: {
          navy: '#0f172a',
        },
        accent: {
          green: '#10b981',
          red: '#f43f5e',
          blue: '#6366f1',
          gold: '#f59e0b',
        },
        retro: {
          bg: '#f8fafc',
          surface: '#ffffff',
          board: '#f1f5f9',
          text: '#1e293b',
          highlight: '#ff6b35'
        },
        muted: {
          1: '#e2e8f0',
          2: '#cbd5e1',
          3: '#94a3b8',
        },
        text: {
          main: '#1e293b',
          muted: '#475569',
          light: '#94a3b8',
        },
      },
      fontFamily: {
        sans: ['"Geist"', '"Segoe UI"', 'Tahoma', 'Geneva', 'Verdana', 'sans-serif'],
        ui: ['"Inter"', '"Segoe UI"', 'Tahoma', 'Geneva', 'Verdana', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
      },
      boxShadow: {
        'card': '0 10px 26px rgba(15, 23, 42, 0.08)',
        'card-hover': '0 16px 38px rgba(15, 23, 42, 0.12)',
        'modal': '0 20px 60px rgba(0, 0, 0, 0.4)',
      },
      borderRadius: {
        '1': '14px',
        '2': '8px',
        '3': '16px',
        'pill': '9999px',
      },
      transitionDuration: {
        'fast': '180ms',
        'medium': '360ms',
        'slow': '500ms',
      },
      transitionTimingFunction: {
        'easing': 'cubic-bezier(0.2, 0.9, 0.3, 1)',
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      maxWidth: {
        'container': '1180px',
      },
    },
  },
  plugins: [],
}



