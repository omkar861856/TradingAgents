/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/index.html",
    "./server.py",
  ],
  theme: {
    extend: {
      colors: {
        sky: {
          500: '#0ea5e9',
        },
        emerald: {
          500: '#10b981',
        },
      },
    },
  },
  safelist: [
    {
      pattern: /text-(emerald|sky|amber|orange|rose)-400/,
    },
    {
      pattern: /border-l-(emerald|sky|amber|orange|rose)-500/,
    },
    {
      pattern: /bg-(emerald|sky|amber|orange|rose)-500/,
    },
    {
      pattern: /shadow-(emerald|sky|amber|orange|rose)-500\/30/,
    },
  ],
  plugins: [],
}
