import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// The same two plugins as the app (frontend/vite.config.js). `fs.allow` lets the dev server
// read the library's Spanish labels, which live in the app and are shared, not copied.
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: { fs: { allow: ['..'] } },
})
