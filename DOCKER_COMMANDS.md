# Docker Commands Reference (Airgapped Environment)

This document provides the equivalent Docker commands for the docker-compose.yml configuration.

## Build the Image

```bash
# For cross-platform compatibility (build on macOS/Windows, run on Linux)
docker build --platform linux/amd64 -t hebrew-rag:latest .

# Alternative: Build for current platform only
docker build -t hebrew-rag:latest .
```

## Run the Container

```bash
docker run -d \
  --name hebrew-rag-system \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 11434:11434 \
  -v "$(pwd)/storage:/app/storage" \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -e OLLAMA_HOST=http://localhost:11434 \
  -e LLM_MODEL=gpt-oss:20b \
  -e EMBEDDING_MODEL=intfloat/multilingual-e5-large \
  -e DOTS_OCR_MODEL=rednote-hilab/dots.ocr \
  -e TESSERACT_LANG=heb+eng \
  -e CHUNK_SIZE=1000 \
  -e CHUNK_OVERLAP=200 \
  -e MAX_FILE_SIZE_MB=100 \
  -e WATCH_DIRECTORY=/app/storage/watch \
  -e SCAN_INTERVAL_SECONDS=3600 \
  -e ENABLE_PERIODIC_INDEXING=true \
  -e CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080 \
  hebrew-rag:latest
```

## Management Commands

### Stop Container
```bash
docker stop hebrew-rag-system
```

### Start Existing Container
```bash
docker start hebrew-rag-system
```

### Restart Container
```bash
docker restart hebrew-rag-system
```

### Remove Container
```bash
docker rm hebrew-rag-system
```

### View Logs
```bash
# View recent logs
docker logs hebrew-rag-system

# Follow logs (real-time)
docker logs -f hebrew-rag-system

# View last 50 lines
docker logs --tail=50 hebrew-rag-system
```

### Execute Commands in Container
```bash
# Open shell
docker exec -it hebrew-rag-system bash

# Run specific command
docker exec -it hebrew-rag-system python3 main.py
```

### Check Container Status
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Check container health
docker inspect hebrew-rag-system | grep -A 10 "Health"
```

## Environment Variables

The container uses these environment variables (equivalent to docker-compose):

- `API_HOST=0.0.0.0` - FastAPI host binding
- `API_PORT=8000` - FastAPI port
- `OLLAMA_HOST=http://localhost:11434` - Ollama service URL
- `LLM_MODEL=gpt-oss:20b` - LLM model name
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large` - Embedding model
- `DOTS_OCR_MODEL=rednote-hilab/dots.ocr` - OCR model
- `TESSERACT_LANG=heb+eng` - Tesseract languages
- `CHUNK_SIZE=1000` - Document chunk size
- `CHUNK_OVERLAP=200` - Chunk overlap
- `MAX_FILE_SIZE_MB=100` - Maximum file size
- `WATCH_DIRECTORY=/app/storage/watch` - File watch directory
- `SCAN_INTERVAL_SECONDS=3600` - Periodic scan interval
- `ENABLE_PERIODIC_INDEXING=true` - Enable periodic indexing
- `CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080` - CORS origins

## Ports

- `8000:8000` - FastAPI backend
- `11434:11434` - Ollama API

## Volumes

- `./storage:/app/storage` - Persistent storage mount

## Health Check

The container includes a health check that tests the FastAPI endpoint:
```bash
curl -f http://localhost:8000/api/v1/health
```

## Quick Start

1. Build the image:
   ```bash
   # For cross-platform compatibility
   docker build --platform linux/amd64 -t hebrew-rag:latest .
   ```

2. Run the container:
   ```bash
   docker run -d --name hebrew-rag-system --restart unless-stopped \
     -p 8000:8000 -p 11434:11434 \
     -v "$(pwd)/storage:/app/storage" \
     -e API_HOST=0.0.0.0 -e API_PORT=8000 \
     -e OLLAMA_HOST=http://localhost:11434 \
     -e LLM_MODEL=gpt-oss:20b \
     -e EMBEDDING_MODEL=intfloat/multilingual-e5-large \
     -e DOTS_OCR_MODEL=rednote-hilab/dots.ocr \
     -e TESSERACT_LANG=heb+eng \
     -e CHUNK_SIZE=1000 -e CHUNK_OVERLAP=200 \
     -e MAX_FILE_SIZE_MB=100 \
     -e WATCH_DIRECTORY=/app/storage/watch \
     -e SCAN_INTERVAL_SECONDS=3600 \
     -e ENABLE_PERIODIC_INDEXING=true \
     -e CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080 \
     hebrew-rag:latest
   ```

3. Check status:
   ```bash
   docker logs hebrew-rag-system
   ```

4. Access the API:
   - Backend: http://localhost:8000
   - Ollama: http://localhost:11434 