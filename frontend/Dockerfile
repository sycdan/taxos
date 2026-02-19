FROM node:20

WORKDIR /app

# Copy package files from frontend directory
COPY package*.json ./
RUN npm ci

# Copy frontend source (proto files must already be generated)
COPY . ./

CMD ["npm", "run", "dev"]
