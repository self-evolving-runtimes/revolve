import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  /*
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:48001',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  */
});



// export default defineConfig({
//   plugins: [react()],
//   // No need for a proxy if same origin
// });
