/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Корпоративный цвет системы
        'corporate': {
          50: '#eff6ff',
          100: '#dbeafe', 
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#0055A5', // Основной корпоративный цвет
          600: '#0047a5',
          700: '#0039a5',
          800: '#002ba5',
          900: '#001da5',
        },
        // Системные цвета
        'success': '#5cb85c',
        'error': '#d9534f',
      },
      fontFamily: {
        'sans': ['Montserrat', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
  safelist: [
    // Корпоративные цвета
    'bg-corporate-50',
    'bg-corporate-100',
    'bg-corporate-500',
    'bg-corporate-600', 
    'bg-corporate-700',
    'text-corporate-500',
    'text-corporate-600',
    'text-corporate-700',
    'border-corporate-500',
    'border-corporate-600',
    'hover:bg-corporate-600',
    'hover:bg-corporate-700',
    // Системные цвета
    'bg-success',
    'bg-error',
    'text-success',
    'text-error',
    'border-success',
    'border-error',
    // Динамические цвета источников (стабилизация purge)
    'border-blue-500','bg-blue-50','text-blue-600','focus:ring-blue-500','bg-blue-100','text-blue-800',
    'border-green-500','bg-green-50','text-green-600','focus:ring-green-500','bg-green-100','text-green-800',
    'border-pink-500','bg-pink-50','text-pink-600','focus:ring-pink-500','bg-pink-100','text-pink-800',
    'border-purple-500','bg-purple-50','text-purple-600','focus:ring-purple-500','bg-purple-100','text-purple-800',
    'border-red-500','bg-red-50','text-red-600','focus:ring-red-500','bg-red-100','text-red-800'
  ]
}