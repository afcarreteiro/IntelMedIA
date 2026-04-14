/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Medical color palette (not high contrast)
        'medical-bg': '#F8F9FA',
        'medical-primary': '#4A90A4',
        'medical-secondary': '#E9ECEF',
        'medical-text': '#495057',
        'medical-warning': '#F5A623',
        'medical-error': '#C45C5C',
        'medical-success': '#6BBF8A',
      },
    },
  },
  plugins: [],
}