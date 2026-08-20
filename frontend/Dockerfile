# Multi-stage Dockerfile for Quiz Platform Frontend
# Builds with Vite, serves with Nginx Alpine
# Optimized for low memory (<50MB RAM)

# Stage 1: Builder - Build frontend assets
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit --no-fund

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Runtime - Nginx Alpine serving static files
FROM nginx:alpine AS runtime

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration (overrides default nginx.conf)
COPY nginx.conf /etc/nginx/nginx.conf

# Create required directories and fix permissions for non-root nginx
RUN mkdir -p /var/run/nginx /var/cache/nginx/client_temp /var/cache/nginx/proxy_temp /var/cache/nginx/fastcgi_temp /var/cache/nginx/uwsgi_temp /var/cache/nginx/scgi_temp && \
    chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx /var/run/nginx

USER nginx

EXPOSE 80

# Health check - uses /health endpoint with curl (more reliable than wget in containers)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost/health > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]