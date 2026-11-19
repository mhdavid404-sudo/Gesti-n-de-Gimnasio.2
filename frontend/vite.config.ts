import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Reenvía /api al servicio "backend" de docker-compose (del lado del
// servidor -- el navegador nunca ve este destino). Esto es lo que permite
// que `frontend/src/api/client.ts` llame a una ruta relativa (/api/v1/...)
// en vez de una URL absoluta con un puerto propio: al quedar todo en el
// MISMO origen, un solo túnel apuntando a localhost:5173 alcanza para
// publicar front y back juntos (ver docs/PUESTA-EN-PRODUCCION.md,
// "Publicar con túnel para demo"). Mismo proxy en "preview" por si algún
// día se usa `vite preview` en vez de `vite dev` (hoy no se usa, ver
// frontend/Dockerfile).
const apiProxy = {
  '/api': {
    target: 'http://backend:8000',
    changeOrigin: true,
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    watch: {
      usePolling: true,
      interval: 300,
    },
    proxy: apiProxy,
  },
  preview: {
    port: 5173,
    host: true,
    proxy: apiProxy,
  },
})
