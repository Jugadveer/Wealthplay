/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          1: '#ff6a2b',
          2: '#f97316',
          50: '#fff7ed',
          100: '#ffedd5',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          primary: '#FF5F3D',
          primaryDark: '#E64A2E',
        },
        accent: {
          green: '#06b6a4',
          red: '#ef4444',
          blue: '#3b82f6',
        },
        muted: {
          1: '#f7f8f9',
          2: '#eef2f4',
          3: '#d1d5db',
        },
        text: {
          main: '#21303a',
          muted: '#6b7b86',
          light: '#9ca3af',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 8px 30px rgba(34, 40, 49, 0.06)',
        'card-hover': '0 12px 40px rgba(34, 40, 49, 0.12)',
        'modal': '0 20px 60px rgba(34, 40, 49, 0.15)',
      },
      borderRadius: {
        '1': '12px',
        '2': '8px',
        '3': '16px',
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


