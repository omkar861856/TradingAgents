import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/blogs': 'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/analyze': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
      '/sitemap.xml': 'http://localhost:8000',
    }
  }
})
