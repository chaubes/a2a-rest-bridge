import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
  preview: {
    port: 3000,
  },
  define: {
    'import.meta.env.VITE_ORDER_AGENT_URL': JSON.stringify(
      process.env.VITE_ORDER_AGENT_URL ?? 'http://localhost:10010'
    ),
  },
})
