/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        surface: "#111827",
        "surface-card": "#182234",
        "surface-border": "#1f2d42",
        primary: {
          50: '#eef6ff',
          100: '#d9ecff',
          200: '#bce0ff',
          300: '#8eccff',
          400: '#59b0ff',
          500: '#308fff',
          600: '#1771f7',
          700: '#115ce4',
          800: '#144bb8',
          900: '#164291',
        },
        fake: {
          DEFAULT: '#f43f5e',
          light: '#fb7185',
          bg: 'rgba(244, 63, 94, 0.12)',
          border: 'rgba(244, 63, 94, 0.3)'
        },
        authentic: {
          DEFAULT: '#10b981',
          light: '#34d399',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.3)'
        }
      },
    },
  },
  plugins: [],
}

