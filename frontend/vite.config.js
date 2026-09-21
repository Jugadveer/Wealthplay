import path from 'path'

import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

const isVercel = process.env.VERCEL === '1' || process.env.VERCEL === 'true'

export default defineConfig(({ mode }) => {
  // Django does not always get port 8000 on a dev machine. Put
  // `API_PROXY=http://127.0.0.1:8001` in frontend/.env to point somewhere else;
  // the default needs no configuration.
  const api = loadEnv(mode, process.cwd(), '').API_PROXY || 'http://127.0.0.1:8000'

  return {
    plugins: [react({ jsxRuntime: 'automatic' })],
    resolve: {
      alias: { '@': path.resolve(__dirname, './src') },
    },
    build: {
      outDir: isVercel ? 'dist' : '../static/react',
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
