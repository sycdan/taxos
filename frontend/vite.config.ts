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
      // Forward Connect-RPC calls to the backend container.
      // The browser always calls the same origin (:5173), so this works
      // regardless of where the browser is — host, devcontainer, CI, etc.
      '/taxos.v1': {
        target: process.env.VITE_GRPC_API_URL || 'http://backend:50051',
        changeOrigin: true,
      },
    },
  },
})
