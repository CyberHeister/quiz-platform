/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./src/**/*.{html,js}",
    "./src/index.html"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f0ff',
          100: '#e0e0ff',
          200: '#c2c2ff',
          300: '#a3a3ff',
          400: '#8585ff',
          500: '#6366f1',
          600: '#5046e5',
          700: '#3f37b9',
          800: '#2e298d',
          900: '#1d1b61'
        }
      }
    }
  },
  plugins: []
}
