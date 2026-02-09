FROM node:20 AS build

WORKDIR /app

# Copy package files from frontend directory
COPY package*.json ./
RUN npm ci

# Copy frontend source (proto files must already be generated)
COPY . ./

CMD ["npm", "run", "dev"]

# Production stage - serve built files
# FROM nginx:alpine

# # Copy built files from build stage
# COPY --from=build /app/dist /usr/share/nginx/html

# # Copy nginx configuration
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# EXPOSE 80

# CMD ["nginx", "-g", "daemon off;"]
