/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Keep cookies first-party in dev: the browser only ever talks to the
      // Vite origin, which forwards to Django server-side. Deliberately NOT
      // setting changeOrigin: it would rewrite the Host header Django sees
      // to the target (localhost:8000), which no longer matches the
      // browser's actual Origin header and breaks Django's same-origin CSRF
      // check, forcing CSRF_TRUSTED_ORIGINS to track the exact dev port.
      // Leaving Host as-is lets Django's own-origin check pass naturally on
      // any Vite port.
      '/api': {
        target: 'http://localhost:8000',
      },
    },
  },
  test: {
    environment: 'jsdom',
    css: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
