# -----------------------------
# Stage 1: Codegen with Buf
# -----------------------------
FROM bufbuild/buf:1.34.0 AS codegen

WORKDIR /workspace

# Copy your proto files
COPY proto/ ./proto/

# Copy your buf config
COPY buf.yaml ./
COPY frontend/buf.gen.yaml ./

# Run codegen
RUN buf generate

# -----------------------------
# Stage 2: Build frontend
# -----------------------------
FROM node:20 AS build

WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Copy generated code from stage 1
COPY --from=codegen /workspace/frontend/src/api ./src/api

# Build Vite app
# RUN npm run build
EXPOSE 5173

CMD ["npm", "run", "dev"]
# -----------------------------
# Stage 3: Runtime container
# -----------------------------
# FROM node:20-alpine

# WORKDIR /app

# COPY --from=build /app/dist ./dist

# EXPOSE 5173

# CMD ["npm", "run", "preview"]
