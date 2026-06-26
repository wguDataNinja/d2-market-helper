import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@data': path.resolve(__dirname, '../data'),
    },
  },
  server: {
    fs: {
      allow: [path.resolve(__dirname, '..')],
    },
  },
  // For GitHub Pages sub-path deployment, change base to '/<repo>/' e.g. '/traderie/'
  // For root-domain deployment (username.github.io), keep as '/'
  base: '/',
})
