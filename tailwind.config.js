/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./Eventio/**/templates/**/*.html'],
  theme: {
    fontFamily: {
        sans: ["Poppins", "sans-serif"],
    },
    extend: {
        colors: {
            'neoviolet': '#b180fb',
            'neoviolet-hover': '#a474ed'
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
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

