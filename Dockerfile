FROM node:20-alpine
WORKDIR /app
COPY api/package*.json ./api/
RUN cd api && npm install
COPY . .
RUN cd api && npx tsc
EXPOSE 3001
CMD ["node", "api/dist/index.js"]
