FROM node:22-alpine AS dev

WORKDIR /app/apps/frontend

COPY apps/frontend/package.json ./package.json
RUN npm install

COPY apps/frontend ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
