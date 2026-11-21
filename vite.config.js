import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'static/bundles',
    emptyOutDir: true,
    rollupOptions: {
      input: 'frontend/about.jsx',
      output: {
        entryFileNames: 'about.js',
        assetFileNames: '[name][extname]',
        inlineDynamicImports: true,
      },
    },
  },
});
