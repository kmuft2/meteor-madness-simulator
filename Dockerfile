# Multi-stage build for React + Python backend
FROM node:18-slim AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Python backend + serve frontend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including Node.js for dev server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    python-dotenv==1.0.0 \
    aiohttp==3.9.1 \
    requests==2.31.0 \
    numpy==1.26.2 \
    && pip cache purge

# Copy backend
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY .env /app/.env

# Copy frontend source (for dev mode) and built files
COPY frontend/ /app/frontend/
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Install frontend dependencies in final image (for dev mode)
WORKDIR /app/frontend
RUN npm install

# Expose ports
EXPOSE 8000 3000

# Create startup script
WORKDIR /app
RUN echo '#!/bin/bash\n\
echo "========================================"\n\
echo "🌍 Meteor Madness Simulator"\n\
echo "NASA Space Apps Challenge 2025"\n\
echo "========================================"\n\
echo ""\n\
echo "Starting services..."\n\
echo ""\n\
# Start backend\n\
cd /app/backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &\n\
BACKEND_PID=$!\n\
echo "✅ Backend API starting on port 8000..."\n\
\n\
# Start React dev server\n\
cd /app/frontend && npm run dev -- --host 0.0.0.0 --port 3000 &\n\
FRONTEND_PID=$!\n\
echo "✅ React app starting on port 3000..."\n\
\n\
sleep 5\n\
\n\
echo ""\n\
echo "========================================"\n\
echo "🚀 Application Ready!"\n\
echo "========================================"\n\
echo ""\n\
echo "  React App:  http://localhost:3000"\n\
echo "  API Docs:   http://localhost:8000/docs"\n\
echo "  API:        http://localhost:8000/api"\n\
echo ""\n\
echo "========================================"\n\
\n\
wait $BACKEND_PID $FRONTEND_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
