import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['localhost', 'cb1ddb63-a871-45c6-8a5d-f6f1852a54e0.preview.emergentagent.com'],
  },
})
