import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allows external access
    port: 5173, // Change as needed
    open: true, // Opens in browser
    watch:{usePolling: true, interval: 100},
    allowedHosts: true
  }
});