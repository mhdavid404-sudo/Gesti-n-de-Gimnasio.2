# frontend/Dockerfile — SmartGym v2, Entrega 1
#
# Imagen de desarrollo (Vite dev server con HMR), NO build de produccion:
# eso esta fuera de alcance en Entrega 1 (COORDINACION-ENTREGA1.md,
# seccion 3, nota para Royer).

FROM node:22-alpine

WORKDIR /app

# Copiamos primero el manifiesto de dependencias para aprovechar la cache
# de capas de Docker (igual que en backend/Dockerfile).
COPY package*.json ./
RUN npm install

# Se copia el resto del codigo para que la imagen sea autocontenida. En
# docker-compose este directorio queda ademas montado como volumen para
# HMR; el propio docker-compose.yml agrega un volumen anonimo sobre
# /app/node_modules para no dejar que el bind mount pise los binarios
# nativos de Linux instalados aqui dentro con los de Windows del host.
COPY . .

EXPOSE 5173

# --host 0.0.0.0 explicito (redundante con host: true ya presente en
# vite.config.ts) para que el servidor sea alcanzable fuera del
# contenedor incluso si vite.config.ts cambiara en el futuro.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
