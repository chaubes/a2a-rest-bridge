# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM node:24-alpine AS builder

WORKDIR /app

# Install dependencies first (layer cached unless package files change)
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

# Copy source and build
COPY . .

# VITE_ORDER_AGENT_URL is baked at build time.
# Pass it as a build arg; fall back to the public default if not supplied.
ARG VITE_ORDER_AGENT_URL=http://localhost:10010
ENV VITE_ORDER_AGENT_URL=${VITE_ORDER_AGENT_URL}

RUN npm run build

# ── Stage 2: serve ────────────────────────────────────────────────────────────
FROM nginx:alpine AS runtime

# Remove the default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Install our custom config (listens on port 3000, SPA fallback)
COPY nginx.conf /etc/nginx/conf.d/agentcart.conf

# Copy built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
