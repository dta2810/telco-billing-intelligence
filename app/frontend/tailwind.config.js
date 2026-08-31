/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        db: {
          bg: '#0a0a0a',         // near-black
          card: '#161616',        // dark grafito
          border: '#2a2a2a',
          text: '#f5f5f5',
          muted: '#a1a1a1',
          accent: '#e60028',      // brand red
          'accent-soft': '#ff3b54',
          green: '#22c55e',
          yellow: '#eab308',
          red: '#ef4444',
          orange: '#f97316',
        },
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #e60028 0%, #b3001f 100%)',
      },
    },
  },
  plugins: [],
};
