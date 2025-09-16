/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mystical: {
          // Brown-black scroll aesthetic per PRD
          dark: '#1b1511',
          darker: '#14100d',
          darkest: '#0f0b08',
          text: '#EDE3D1',
          'text-secondary': '#D9CBB3',
          muted: '#AC9B84',
          accent: '#D4AF37',
          'accent-hover': '#E0C170',
          'accent-light': '#F2D49E',
          'accent-dark': '#8C6D1F',
          border: '#5C4634',
          'border-light': '#6E5642',
          gold: '#D4AF37',
          copper: '#B87333',
          void: '#22160F',
        }
      },
      fontFamily: {
        mystical: ['Segoe UI', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'mystical': '0 8px 32px rgba(0, 0, 0, 0.4)',
        'mystical-lg': '0 20px 40px rgba(0, 0, 0, 0.5)',
        // Shift glow tones from purple to gold/copper
        'mystical-glow': '0 0 20px rgba(212, 175, 55, 0.35)',
        'mystical-glow-intense': '0 0 30px rgba(212, 175, 55, 0.5)',
        'mystical-glow-gold': '0 0 18px rgba(212, 175, 55, 0.45)',
      },
      animation: {
        'mystical-float': 'mysticalFloat 6s ease-in-out infinite',
        'mystical-pulse': 'mysticalPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'mystical-shimmer': 'mysticalShimmer 2s infinite',
      },
      keyframes: {
        mysticalFloat: {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '33%': { transform: 'translateY(-10px) rotate(1deg)' },
          '66%': { transform: 'translateY(-5px) rotate(-1deg)' },
        },
        mysticalPulse: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(1.05)' },
        },
        mysticalShimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
    },
  },
  plugins: [],
}
