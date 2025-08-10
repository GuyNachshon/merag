# Frontend-Only Deployment Guide

This guide shows how to deploy just the frontend service to work with your existing backend.

## Prerequisites

1. **Backend must be running** on `http://localhost:8000`
2. **Docker must be installed** and running
3. **Frontend code** must be in the `frontend/` directory

## Quick Start

### Option 1: Using the deployment script
```bash
./deploy-frontend-only.sh
```

### Option 2: Using Docker Compose
```bash
docker-compose -f docker-compose.frontend-only.yml up -d
```

### Option 3: Manual Docker commands
```bash
# Build the frontend image
cd frontend
docker build -t hebrew-rag-frontend:latest .

# Run the frontend container
docker run -d \
    --name hebrew-rag-frontend \
    --restart unless-stopped \
    -p 3000:3000 \
    -e VITE_API_URL=http://localhost:8000 \
    hebrew-rag-frontend:latest
```

## Verification

After deployment, you should be able to access:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000 (should already be running)

## Management Commands

### View logs
```bash
docker logs hebrew-rag-frontend
```

### Stop frontend
```bash
docker stop hebrew-rag-frontend
```

### Restart frontend
```bash
docker restart hebrew-rag-frontend
```

### Remove frontend
```bash
docker rm hebrew-rag-frontend
```

### Update frontend (rebuild)
```bash
# Stop and remove old container
docker stop hebrew-rag-frontend && docker rm hebrew-rag-frontend

# Rebuild and start
./deploy-frontend-only.sh
```

## Troubleshooting

### Frontend can't connect to backend
1. Check if backend is running: `curl http://localhost:8000/api/v1/health`
2. Verify the API URL in the frontend container: `docker exec hebrew-rag-frontend env | grep VITE`
3. Check frontend logs: `docker logs hebrew-rag-frontend`

### Port 3000 already in use
```bash
# Find what's using port 3000
lsof -i :3000

# Stop the conflicting service or use a different port
docker run -d --name hebrew-rag-frontend -p 3001:3000 hebrew-rag-frontend:latest
```

### Frontend build fails
1. Check if Node.js dependencies are installed: `cd frontend && npm install`
2. Check for build errors: `cd frontend && npm run build`
3. Verify the frontend code is complete

## Configuration

The frontend connects to the backend using the `VITE_API_URL` environment variable:

- **Default**: `http://localhost:8000`
- **Custom**: Set `-e VITE_API_URL=http://your-backend-url:8000`

## Architecture

```
┌─────────────────┐    HTTP    ┌─────────────────┐
│   Frontend      │ ────────── │    Backend      │
│   Port 3000     │            │   Port 8000     │
│                 │            │                 │
│  Vue.js App     │            │  FastAPI App    │
│  (Container)    │            │  (Container)    │
└─────────────────┘            └─────────────────┘
```

The frontend and backend are completely independent containers that communicate over HTTP. 