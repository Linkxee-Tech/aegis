/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: '#0B0D0F',
          900: '#101316',
          800: '#161A1F',
          700: '#1A1E23',
          600: '#23282F',
          500: '#2E3540',
        },
        bone: {
          100: '#F2F0EB',
          300: '#C9C6BD',
          500: '#8C8A82',
        },
        signal: {
          detective: '#4D9FFF',
          diagnostician: '#A87CFF',
          remediation: '#4ADE80',
          reporter: '#FFB454',
          amber: '#FF8A3D',
          danger: '#FF5C5C',
        },
      },
      fontFamily: {
        display: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(255,138,61,0.15), 0 0 24px rgba(255,138,61,0.12)',
      },
      animation: {
        'pulse-slow': 'pulse-slow 2.6s ease-in-out infinite',
        trace: 'trace 2.4s linear infinite',
        blink: 'blink 1.4s ease-in-out infinite',
      },
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { opacity: '0.55' },
          '50%': { opacity: '1' },
        },
        trace: {
          '0%': { strokeDashoffset: '0' },
          '100%': { strokeDashoffset: '-240' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.25' },
        },
      },
    },
  },
  plugins: [],
}
