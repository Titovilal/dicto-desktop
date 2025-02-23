/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{ts,tsx}',
    './src/renderer/src/**/*.{ts,tsx}'
    // Asegúrate de incluir todos los directorios donde tienes componentes
  ],
  theme: {
    extend: {}
  },
  plugins: []
}
