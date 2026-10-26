/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0b1220',
          900: '#111827',
          800: '#1a2332',
          700: '#243044',
        },
        accent: {
          DEFAULT: '#6366f1',
          muted: '#818cf8',
        },
        verify: {
          ok: '#22c55e',
          fail: '#ef4444',
          pending: '#f59e0b',
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};
