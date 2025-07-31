# Stage 1: Build the Next.js app
FROM node:22-alpine AS build

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Optional: Copy config files
COPY next.config.ts ./
COPY tsconfig.json ./

# Copy environment file
COPY .env ./

# Set environment variables
ARG REACT_APP_API_URL=http://backend:8000
ARG REACT_APP_LLM_API_URL=http://llm:8001
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
ENV REACT_APP_LLM_API_URL=${REACT_APP_LLM_API_URL}

# Copy source code
COPY . .

# Run the build command
RUN npm run build

# Stage 2: Run the app using Node.js
FROM node:22-alpine

# Set working directory
WORKDIR /app

# Copy built output from the build stage
COPY --from=build /app/next.config.ts ./
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/package.json ./
COPY --from=build /app/.env ./
COPY --from=build /app/tsconfig.json ./

# Install minimal runtime dependencies
RUN npm install --production

# Expose port
EXPOSE 3000

# Start the Next.js app
CMD ["npm", "run", "start"]