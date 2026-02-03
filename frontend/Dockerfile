FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY index.html vite.config.ts ./
COPY tsconfig*.json ./
COPY public/ ./public/
COPY src/ ./src/

EXPOSE 5173

CMD ["npm", "run", "dev"]
