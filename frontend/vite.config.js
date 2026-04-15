import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      // All /chat, /analyze, /analytics, /uploads, /rank requests → FastAPI
      '/chat':      { target: 'http://localhost:8000', changeOrigin: true },
      '/analyze':   { target: 'http://localhost:8000', changeOrigin: true },
      '/analytics': { target: 'http://localhost:8000', changeOrigin: true },
      '/uploads':   { target: 'http://localhost:8000', changeOrigin: true },
      '/rank':      { target: 'http://localhost:8000', changeOrigin: true },
      '/health':    { target: 'http://localhost:8000', changeOrigin: true },
      '/news':      { target: 'http://localhost:8000', changeOrigin: true },
      '/dashboard': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})


