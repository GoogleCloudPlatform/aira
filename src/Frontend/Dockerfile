# Get PNPM packages
FROM node:20-alpine AS deps
RUN apk update && apk add --no-cache libc6-compat
RUN corepack enable && corepack prepare pnpm@9.0.2 --activate 
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --only=production --frozen-lockfile

# Rebuild the source code only when needed
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@9.0.2 --activate
#Set environment Variable
ARG NEXT_PUBLIC_FIREBASE_API_KEY
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ARG NEXT_PUBLIC_FIREBASE_APP_ID
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_TUTORIAL_BUCKET
ENV NEXT_PUBLIC_LOOKER=liabi.cloud.looker.com
ENV NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID=1
ENV NEXT_PUBLIC_DEFAULT_THEME=
RUN touch .env
RUN echo "NEXT_PUBLIC_FIREBASE_API_KEY=$NEXT_PUBLIC_FIREBASE_API_KEY" >> .env
RUN echo "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN" >> .env
RUN echo "NEXT_PUBLIC_FIREBASE_APP_ID=$NEXT_PUBLIC_FIREBASE_APP_ID" >> .env
RUN echo "NEXT_PUBLIC_FIREBASE_PROJECT_ID=$NEXT_PUBLIC_FIREBASE_PROJECT_ID" >> .env
RUN echo "NEXT_PUBLIC_LOOKER=$NEXT_PUBLIC_LOOKER" >> .env
RUN echo "NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID=$NEXT_PUBLIC_LOOKER_GENERAL_DASHBOARD_ID" >> .env
RUN echo "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL" >> .env
RUN echo "NEXT_PUBLIC_TUTORIAL_BUCKET=$NEXT_PUBLIC_TUTORIAL_BUCKET" >> .env

RUN cat .env
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN pnpm build

# Production image, copy all the files and run next
FROM node:20-alpine AS runner
RUN corepack enable && corepack prepare pnpm@9.0.2 --activate
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json


RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
RUN chown -R nextjs:nodejs /app/.next
USER nextjs

EXPOSE 3000

ENTRYPOINT ["pnpm", "start"]