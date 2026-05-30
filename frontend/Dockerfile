FROM node:22-alpine AS deps
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app/frontend
COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend ./
COPY fixtures /app/fixtures
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV FIXTURES_ROOT=/app/fixtures
COPY --from=builder /app/frontend/.next/standalone ./
COPY --from=builder /app/frontend/.next/static ./.next/static
COPY fixtures ./fixtures
EXPOSE 3000
CMD ["node", "server.js"]
