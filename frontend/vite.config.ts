import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['.local', '.lan', 'taxos.wildharvesthomestead.com', 'frontend'],
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true,
      interval: 1000
    },
    hmr: {
      host: 'localhost',
      port: 5173
    },
    proxy: {
      // GraphQL API (new)
      '/graphql': {
        target: process.env.VITE_API_URL || 'http://backend:50052',
        changeOrigin: true,
      },
      // File download endpoint (new)
      '/files': {
        target: process.env.VITE_API_URL || 'http://backend:50052',
        changeOrigin: true,
      },
      // Connect-RPC (kept until Phase 9 cleanup)
      '/taxos.v1': {
        target: process.env.VITE_GRPC_API_URL || 'http://backend:50051',
        changeOrigin: true,
      },
    },
  },
})
