/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fdf4f3',
          100: '#fce8e6',
          200: '#f9d5d2',
          300: '#f4b5af',
          400: '#ec8b82',
          500: '#e05d51',
          600: '#cc4237',
          700: '#ab342b',
          800: '#8e2f28',
          900: '#762d27',
          950: '#401410',
        },
        secondary: {
          50: '#f5f7fa',
          100: '#ebeef3',
          200: '#d2dae5',
          300: '#aab9ce',
          400: '#7c93b2',
          500: '#5b7599',
          600: '#475d7f',
          700: '#3a4c67',
          800: '#334157',
          900: '#2e394a',
          950: '#1e2531',
        },
      },
    },
  },
  plugins: [],
}
