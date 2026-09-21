import path from 'path'

import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// Where Django serves the built bundle from. The generated index.html has to
// reference `/static/react/assets/...` rather than `/assets/...`, because
// WhiteNoise serves everything under STATIC_URL and a root-relative asset path
// 404s in production. Nothing catches this in development: the dev server
// serves its own index.html and Django's copy is never rendered.
const BASE = '/static/react/'

export default defineConfig(({ command, mode }) => {
  // Django does not always get port 8000 on a dev machine. Put
  // `API_PROXY=http://127.0.0.1:8001` in frontend/.env to point somewhere else;
  // the default needs no configuration.
  const api = loadEnv(mode, process.cwd(), '').API_PROXY || 'http://127.0.0.1:8000'

  return {
    // Only for the build. The dev server serves from the root, and prefixing it
    // there would make every route 404 behind the proxy.
    base: command === 'build' ? BASE : '/',
    plugins: [react({ jsxRuntime: 'automatic' })],
    resolve: {
      alias: { '@': path.resolve(__dirname, './src') },
    },
    build: {
      // Always the same place. Django serves this directory in every
      // environment, including on Vercel, where one function serves the API and
      // the page together rather than splitting them across two origins.
      outDir: '../static/react',
      emptyOutDir: true,
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: { 'react-vendor': ['react', 'react-dom', 'react-router-dom'] },
        },
      },
    },
    server: {
      port: 3000,
      proxy: {
        '/api': { target: api, changeOrigin: true },
      },
    },
  }
})
