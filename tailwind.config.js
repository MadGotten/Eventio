/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./Eventio/**/templates/**/*.html', './Eventio/static/js/**/*.js'],
  theme: {
    fontFamily: {
        sans: ["Poppins", "sans-serif"],
    },
    extend: {
        colors: {
            'neoviolet': '#b180fb',
            'neoviolet-hover': '#a474ed',
            'neutral-350': '#b8b8b8'
        },
        typography: {
            DEFAULT: {
                css: {
                    'ul > li::marker': {
                        color: 'inherit',
                    },
                },
            },
        },
        borderRadius: {
            DEFAULT: '5px'
        },
        boxShadow: {
            light: '4px 4px 0px 0px #000',
            dark: '4px 4px 0px 0px #000',
        },
        keyframes: {
            'fade-in': {
              '0%': { opacity: 0.001 },
              '100%': { opacity: 1 },
            }
        },
        animation: {
            'fade-in': 'fade-in 0.1s ease-in-out',
        }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

