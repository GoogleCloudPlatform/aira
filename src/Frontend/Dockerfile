# Get PNPM packages
FROM node:16-alpine AS deps
RUN apk update && apk add --no-cache libc6-compat
RUN corepack enable && corepack prepare pnpm@8.6.5 --activate 
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --only=production --frozen-lockfile

# Rebuild the source code only when needed
FROM node:16-alpine AS builder
RUN corepack enable && corepack prepare pnpm@8.6.5 --activate
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN pnpm build

# Production image, copy all the files and run next
FROM node:16-alpine AS runner
RUN corepack enable && corepack prepare pnpm@8.6.5 --activate
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next-i18next.config.js ./next-i18next.config.js 
COPY --from=builder /app/next.config.js ./next.config.js 
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json


RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
RUN chown -R nextjs:nodejs /app/.next
USER nextjs

EXPOSE 3000

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry.
# ENV NEXT_TELEMETRY_DISABLED 1

ENTRYPOINT ["pnpm", "start"]