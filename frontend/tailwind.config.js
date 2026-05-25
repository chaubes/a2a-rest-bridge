/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc8fb',
          400: '#36aaf6',
          500: '#0c8ee7',
          600: '#0070c5',
          700: '#0059a0',
          800: '#044c84',
          900: '#09406d',
        },
      },
      animation: {
        'bounce-dot': 'bounce 1s infinite',
      },
    },
  },
  plugins: [],
}
