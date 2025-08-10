#!/bin/bash

set -e

echo "🚀 Deploying Hebrew RAG System (Airgapped)"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker is running and start it if needed
if ! docker info &> /dev/null; then
    print_warning "Docker is not running. Attempting to start Docker..."
    
    # Try different methods to start Docker
    if command -v systemctl &> /dev/null; then
        print_status "Starting Docker with systemctl..."
        sudo systemctl start docker
        sleep 3
    elif command -v service &> /dev/null; then
        print_status "Starting Docker with service..."
        sudo service docker start
        sleep 3
    elif command -v dockerd &> /dev/null; then
        print_status "Starting Docker daemon..."
        sudo dockerd &
        sleep 5
    else
        print_error "Could not start Docker automatically. Please start Docker manually."
        print_status "Common commands:"
        print_status "  - sudo systemctl start docker"
        print_status "  - sudo service docker start"
        print_status "  - sudo dockerd &"
        exit 1
    fi
    
    # Check if Docker started successfully
    if docker info &> /dev/null; then
        print_success "Docker started successfully"
    else
        print_error "Failed to start Docker. Please start it manually."
        exit 1
    fi
else
    print_success "Docker is already running"
fi

# Load the Docker image
print_status "Loading Docker image..."
# check if docker guychuk/hebrew-rag-airgapped already in docker images if not, load tar - docker load -i hebrew-rag-airgapped-package.tar
if docker images | grep -q "guychuk/hebrew-rag-airgapped"; then
    # tag it as hebrew-rag-system so we can run     docker stop hebrew-rag-system 2>/dev/null || true
                                                    #    docker rm hebrew-rag-system 2>/dev/null || true
    docker tag guychuk/hebrew-rag-airgapped hebrew-rag-airgapped:latest
    print_success "Docker image already exists"
else
    if [ ! -f hebrew-rag-airgapped-package.tar ]; then
        print_error "Docker image tar file not found! Please ensure hebrew-rag-airgapped-package.tar is in the current directory."
        exit 1
    fi
    docker load -i hebrew-rag-airgapped-package.tar
    if [ $? -ne 0 ]; then
        print_error "Failed to load Docker image from tar file!"
        exit 1
    fi
fi


if [ $? -ne 0 ]; then
    print_error "Failed to load Docker image!"
    exit 1
fi

print_success "Docker image loaded successfully"

# Stop and remove existing container if it exists
print_status "Checking for existing container..."
if docker ps -a --format 'table {{.Names}}' | grep -q "^hebrew-rag-system$"; then
    print_status "Stopping existing container..."
    docker stop hebrew-rag-system 2>/dev/null || true
    docker rm hebrew-rag-system 2>/dev/null || true
    print_success "Existing container removed"
fi

# Create storage directories
print_status "Creating storage directories..."
mkdir -p storage/uploads
mkdir -p storage/qdrant
mkdir -p storage/vector_db
mkdir -p storage/watch
mkdir -p storage/fastembed_cache

print_success "Storage directories created"

# Start the services
print_status "Starting Hebrew RAG System..."
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
  hebrew-rag-airgapped:latest
if [ $? -ne 0 ]; then
    print_error "Failed to start services!"
    exit 1
fi
print_success "Services started successfully"

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check health
print_status "Checking service health..."
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    print_success "Hebrew RAG System is running and healthy!"
    echo ""
    echo "🌐 Access the application at: http://localhost:8000"
    echo "📚 API documentation at: http://localhost:8000/docs"
    echo "🔍 Health check at: http://localhost:8000/api/v1/health"
    echo ""
    echo "📁 Upload documents to: ./storage/watch/"
    echo "💾 Data is stored in: ./storage/"
    echo ""
    echo "🛑 To stop the system: docker stop hebrew-rag-system"
    echo "📊 To view logs: docker logs -f hebrew-rag-system"
    echo "🔄 To restart: docker restart hebrew-rag-system"
else
    print_error "Service health check failed!"
    print_status "Checking logs..."
    docker logs --tail=50 hebrew-rag-system
    exit 1
fi
