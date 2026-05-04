# Stage 1: Build frontend
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps

COPY frontend/ .

ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Stage 2: Backend + serve frontend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code and install
COPY backend/ ./backend/
RUN pip install --no-cache-dir ./backend

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Clean stale bytecode
RUN find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

ENV PYTHONPATH=/app/backend
ENV PORT=8000
EXPOSE ${PORT}

CMD cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
