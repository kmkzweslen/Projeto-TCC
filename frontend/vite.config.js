import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// A porta 5173 precisa bater com FRONTEND_URL no .env do back-end,
// porque o login da Meta volta para http://localhost:5173/#token=...
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
  },
})
