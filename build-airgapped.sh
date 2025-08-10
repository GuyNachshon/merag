#!/bin/bash

set -e

echo "🚀 Building Airgapped Hebrew RAG System Package"
echo "================================================"

# Configuration
IMAGE_NAME="hebrew-rag-airgapped"
PACKAGE_NAME="hebrew-rag-airgapped-package"
TAR_FILE="${PACKAGE_NAME}.tar"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
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

# Check if Docker is running and accessible
if ! docker info &> /dev/null; then
    print_warning "Docker info check failed. Checking Docker status..."
    
    # Check if Docker daemon is running
    if pgrep -f dockerd > /dev/null 2>&1; then
        print_status "Docker daemon is running but not accessible to current user"
        print_status "This is usually a permission issue. Trying to fix..."
        
        # Check if user is in docker group
        if ! groups | grep -q docker; then
            print_warning "User is not in docker group. Adding user to docker group..."
            print_status "You may need to log out and back in for this to take effect"
            sudo usermod -aG docker $USER
        fi
        
        # Try to start Docker service if not running
        if ! sudo systemctl is-active --quiet docker; then
            print_status "Starting Docker service..."
            sudo systemctl start docker
            sleep 3
        fi
        
        # Check again
        if docker info &> /dev/null; then
            print_success "Docker is now accessible"
        else
            print_error "Docker is running but still not accessible"
            print_status "Try one of these solutions:"
            print_status "1. Log out and log back in"
            print_status "2. Run: sudo usermod -aG docker $USER"
            print_status "3. Run: newgrp docker"
            print_status "4. Use: sudo docker info (for this session)"
            exit 1
        fi
    else
        print_warning "Docker daemon is not running. Attempting to start Docker..."
        
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
    fi
else
    print_success "Docker is accessible and running"
fi

# Extract Ollama models first (with smart caching)
print_status "Checking Ollama model extraction..."
if [ -f "extract_ollama_model.sh" ]; then
    chmod +x extract_ollama_model.sh
    
    # Check if we need to re-extract the model
    NEED_EXTRACTION=true
    
    if [ -d "ollama-models" ] && [ -f "ollama-gpt-oss-model.tar.gz" ]; then
        print_status "Checking if model extraction is up to date..."
        
        # Find the newest file in the source model directory
        SOURCE_MODEL_DIR="/usr/share/ollama/.ollama/models"
        if [ -d "$SOURCE_MODEL_DIR" ]; then
            NEWEST_SOURCE=$(find "$SOURCE_MODEL_DIR" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
            SOURCE_TIME=$(stat -c %Y "$NEWEST_SOURCE" 2>/dev/null || echo "0")
        else
            SOURCE_TIME="0"
        fi
        
        # Get the time of our extracted package
        PACKAGE_TIME=$(stat -c %Y "ollama-gpt-oss-model.tar.gz" 2>/dev/null || echo "0")
        
        if [ "$SOURCE_TIME" -le "$PACKAGE_TIME" ]; then
            print_success "Model extraction is up to date (package: $(date -d @$PACKAGE_TIME), source: $(date -d @$SOURCE_TIME))"
            NEED_EXTRACTION=false
        else
            print_status "Model source is newer than package, re-extracting..."
            print_status "Source last modified: $(date -d @$SOURCE_TIME)"
            print_status "Package last modified: $(date -d @$PACKAGE_TIME)"
        fi
    else
        print_status "No existing model extraction found, extracting..."
    fi
    
    if [ "$NEED_EXTRACTION" = true ]; then
        ./extract_ollama_model.sh
        print_success "Ollama models extracted successfully"
    fi
else
    print_warning "extract_ollama_model.sh not found, skipping Ollama model extraction"
fi

# Clean up previous builds
print_status "Cleaning up previous builds..."
rm -rf ${PACKAGE_NAME}
rm -f ${TAR_FILE}
docker rmi ${IMAGE_NAME} 2>/dev/null || true

# Create package directory
print_status "Creating package directory..."
mkdir -p ${PACKAGE_NAME}

# Build the Docker image
print_status "Building Docker image for Linux AMD64 (this may take 30-60 minutes)..."
print_warning "This will download large ML models. Ensure you have stable internet connection."

docker build --platform linux/amd64 -f Dockerfile.airgapped -t ${IMAGE_NAME} . --no-cache

if [ $? -ne 0 ]; then
    print_error "Docker build failed!"
    exit 1
fi

print_success "Docker image built successfully"

# Save the image to tar file
print_status "Saving Docker image to tar file..."
docker save ${IMAGE_NAME} -o ${PACKAGE_NAME}/${TAR_FILE}

if [ $? -ne 0 ]; then
    print_error "Failed to save Docker image!"
    exit 1
fi

print_success "Docker image saved to ${PACKAGE_NAME}/${TAR_FILE}"

# Copy deployment files
print_status "Copying deployment files..."

# Copy data management script
if [ -f "manage_data.sh" ]; then
    cp manage_data.sh ${PACKAGE_NAME}/
    chmod +x ${PACKAGE_NAME}/manage_data.sh
    print_success "Data management script included"
else
    print_warning "manage_data.sh not found, skipping"
fi

# Create deployment script
cat > ${PACKAGE_NAME}/deploy.sh << 'EOF'
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

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is available and running"

# Load the Docker image
print_status "Loading Docker image..."
docker load -i hebrew-rag-airgapped-package.tar

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

# Load Ollama models if available
if [ -d "ollama-models" ] && [ -f "ollama-models/load_model.sh" ]; then
    print_status "Loading Ollama models..."
    if command -v ollama &> /dev/null; then
        cd ollama-models
        ./load_model.sh
        cd ..
        print_success "Ollama models loaded successfully"
    else
        print_warning "Ollama not found on host, models will be loaded in container"
    fi
else
    print_warning "Ollama models not found, LLM features may not work"
fi

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
print_status "This may take 2-3 minutes for first startup..."

# Wait longer for initialization and retry health check
for i in {1..12}; do
    print_status "Health check attempt $i/12..."
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        print_success "Health check passed!"
        break
    fi
    if [ $i -eq 12 ]; then
        print_error "Service health check failed after 6 minutes!"
        print_status "Checking logs..."
        docker logs --tail=50 hebrew-rag-system
        print_status "Trying to get health response for debugging..."
        curl -v http://localhost:8000/api/v1/health || true
        exit 1
    fi
    print_status "Service not ready yet, waiting 30 seconds..."
    sleep 30
done

# Final health check
print_status "Performing final health check..."
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
EOF

chmod +x ${PACKAGE_NAME}/deploy.sh

# Create README
cat > ${PACKAGE_NAME}/README.md << 'EOF'
# Hebrew RAG System - Airgapped Deployment

Complete Hebrew Agentic RAG system for airgapped environments.

## Quick Start

1. **Extract and deploy**:
   ```bash
   tar -xzf hebrew-rag-airgapped-package.tar.gz
   cd hebrew-rag-airgapped-package
   ./deploy.sh
   ```

2. **Access the system**:
   - Web interface: http://localhost:8000
   - API docs: http://localhost:8000/docs

## Data Management

### Manual Processing
```bash
# Copy files for processing
./manage_data.sh copy-to-watch /path/to/documents

# Check status
./manage_data.sh status
```

### Automated Processing
```bash
# Schedule hourly copying
./manage_data.sh schedule /path/to/documents hourly

# Schedule daily copying (2 AM)
./manage_data.sh schedule /path/to/documents daily

# Remove automation
./manage_data.sh unschedule
```

### Backup & Restore
```bash
# Create backup
./manage_data.sh backup

# Restore from backup
./manage_data.sh restore backup-name
```

## System Management

### Service Control
```bash
# Start/stop
docker start hebrew-rag-system
docker stop hebrew-rag-system

# View logs
docker logs -f hebrew-rag-system

# Restart
docker restart hebrew-rag-system
```

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

## Storage Structure
```
storage/
├── uploads/          # User uploaded files
├── qdrant/          # Vector database
├── watch/           # Auto-processing directory
├── vector_db/       # Additional storage
└── fastembed_cache/ # Model cache
```

## Features
- **Hebrew RAG**: Local LLM with Hebrew support
- **OCR**: Hebrew/English text extraction
- **Auto-indexing**: Monitor directories for new files
- **Smart copying**: Only process new/changed files
- **Backup system**: Complete data protection
- **Cron automation**: Scheduled file processing

## Requirements
- Linux with Docker
- 8GB RAM minimum (16GB recommended)
- 50GB disk space
- No internet required after deployment
EOF

# Create .env template
cat > ${PACKAGE_NAME}/.env.template << 'EOF'
# Hebrew RAG System Configuration
# Copy this file to .env and modify as needed

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# LLM Configuration
LLM_MODEL=gpt-oss:20b
OLLAMA_HOST=http://localhost:11434

# Embedding Configuration
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# OCR Configuration
DOTS_OCR_MODEL=rednote-hilab/dots.ocr
TESSERACT_LANG=heb+eng

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=100

# Periodic Indexing
WATCH_DIRECTORY=./storage/watch
SCAN_INTERVAL_SECONDS=3600
ENABLE_PERIODIC_INDEXING=true

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
EOF

# Create package info
cat > ${PACKAGE_NAME}/PACKAGE_INFO.txt << EOF
Hebrew RAG System - Airgapped Package
====================================

Package created: $(date)
Docker image: ${IMAGE_NAME}
Package size: $(du -sh ${PACKAGE_NAME} | cut -f1)

Contents:
- Docker image with all dependencies and models
- Deployment scripts
- Data management script (manage_data.sh)
- Configuration templates
- Documentation

Models included:
- FastEmbed: intfloat/multilingual-e5-large (~2GB)
- Whisper: ivrit-ai/whisper-large-v3 (~3GB)
- Dots.OCR: rednote-hilab/dots.ocr (~7GB)
- Ollama: gpt-oss:20b (~40GB)
- Tesseract: Hebrew + English language packs

Total estimated size: ~60GB

Quick Deploy:
1. tar -xzf hebrew-rag-airgapped-package.tar.gz
2. cd hebrew-rag-airgapped-package
3. ./deploy.sh
4. Access: http://localhost:8000

Data Management:
- ./manage_data.sh copy-to-watch /path/to/docs
- ./manage_data.sh schedule /path/to/docs hourly
- ./manage_data.sh backup
EOF

# Create final tar.gz package
print_status "Creating final package..."
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}/

if [ $? -ne 0 ]; then
    print_error "Failed to create final package!"
    exit 1
fi

# Clean up
rm -rf ${PACKAGE_NAME}

# Show package info
PACKAGE_SIZE=$(du -sh ${PACKAGE_NAME}.tar.gz | cut -f1)

print_success "Airgapped package created successfully!"
echo ""
echo "📦 Package: ${PACKAGE_NAME}.tar.gz"
echo "📏 Size: ${PACKAGE_SIZE}"
echo ""
echo "🚀 To deploy in airgapped environment:"
echo "   1. Copy ${PACKAGE_NAME}.tar.gz to target machine"
echo "   2. Extract: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "   3. Deploy: cd ${PACKAGE_NAME} && ./deploy.sh"
echo ""
echo "✅ Package is ready for airgapped deployment!"