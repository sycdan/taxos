FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig*.json ./
COPY frontend/public/ ./public/
COPY frontend/src/ ./src/

COPY proto/ ./proto/

EXPOSE 5173

CMD ["npm", "run", "dev"]
