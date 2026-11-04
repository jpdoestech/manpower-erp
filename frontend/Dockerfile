FROM node:24-bookworm-slim
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci && chown -R node:node /app
COPY frontend/ ./
USER node
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
