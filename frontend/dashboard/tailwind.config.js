/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neural: {
          blue: '#0066FF',
          purple: '#7C3AED',
          cyan: '#00CED1',
          gold: '#FFD700',
          pink: '#FF006E',
          green: '#00FF41',
          'deep-space': '#0A0E27',
          'nebula-pink': '#FF006E',
          'plasma-green': '#00FF41',
          'void-black': '#000000'
        }
      },
      animation: {
        'synapse-pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'neural-flicker': 'flicker 3s ease-in-out infinite alternate',
        'quantum-shift': 'transform 0.5s ease-in-out',
        'consciousness-breathe': 'breathe 4s ease-in-out infinite'
      },
      keyframes: {
        pulse: {
          '0%, 100%': { opacity: '0.8' },
          '50%': { opacity: '1' }
        },
        flicker: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' }
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' }
        }
      }
    },
  },
  plugins: [],
}
