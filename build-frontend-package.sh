#!/bin/bash

# Build frontend package for Linux deployment
# Handles cross-platform compatibility (Mac M1 → Linux AMD64)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Frontend Package Builder${NC}"
    echo -e "${BLUE}  (Mac M1 → Linux AMD64)${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_header

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running!"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    print_error "Frontend directory not found!"
    exit 1
fi

# Check if Docker Buildx is available
print_status "Checking Docker Buildx..."
if ! docker buildx version >/dev/null 2>&1; then
    print_error "Docker Buildx is not available!"
    echo "Please enable Docker Buildx or update Docker Desktop"
    exit 1
fi

# Create buildx builder if it doesn't exist
print_status "Setting up multi-platform builder..."
if ! docker buildx inspect hebrew-rag-builder >/dev/null 2>&1; then
    docker buildx create --name hebrew-rag-builder --use
    print_success "Created buildx builder: hebrew-rag-builder"
else
    docker buildx use hebrew-rag-builder
    print_success "Using existing buildx builder: hebrew-rag-builder"
fi

# Build the frontend image for Linux AMD64
print_status "Building frontend image for Linux AMD64..."
cd frontend

# Build multi-platform image (but we only need AMD64)
docker buildx build \
    --platform linux/amd64 \
    --tag hebrew-rag-frontend:latest \
    --tag hebrew-rag-frontend:linux-amd64 \
    --load \
    .

print_success "Frontend image built for Linux AMD64"

# Create package directory
PACKAGE_NAME="hebrew-rag-frontend-package"
print_status "Creating package directory..."
rm -rf $PACKAGE_NAME
mkdir -p $PACKAGE_NAME

# Save the Docker image
print_status "Saving Docker image..."
docker save hebrew-rag-frontend:linux-amd64 | gzip > $PACKAGE_NAME/hebrew-rag-frontend.tar.gz

# Create deployment script
print_status "Creating deployment script..."
cat > $PACKAGE_NAME/deploy.sh << 'EOF'
#!/bin/bash

# Frontend deployment script for Linux
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_status "Deploying Hebrew RAG Frontend..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running!"
    exit 1
fi

# Load the Docker image
print_status "Loading Docker image..."
docker load < hebrew-rag-frontend.tar.gz

# Check if backend is running
print_status "Checking if backend is running..."
if ! curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    print_warning "Backend is not running on http://localhost:8000"
    print_warning "Please start the backend first, then run this script again."
    echo ""
    echo "To start the backend:"
    echo "  • If using airgapped: cd hebrew-rag-airgapped-package && ./deploy.sh"
    echo "  • Or start your existing backend container"
    echo ""
    echo "Press Enter to continue anyway, or Ctrl+C to abort..."
    read -r
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "hebrew-rag-frontend"; then
    print_status "Stopping existing frontend container..."
    docker stop hebrew-rag-frontend || true
    docker rm hebrew-rag-frontend || true
fi

# Run the frontend container
print_status "Starting frontend container..."
docker run -d \
    --name hebrew-rag-frontend \
    --restart unless-stopped \
    -p 3000:3000 \
    --add-host=host.docker.internal:host-gateway \
    hebrew-rag-frontend:linux-amd64

print_success "Frontend deployed successfully!"
echo ""
echo "🌐 Frontend is now available at: http://localhost:3000"
echo "🔗 Backend API should be running at: http://localhost:8000"
echo ""
echo "📋 Useful commands:"
echo "  • View frontend logs: docker logs hebrew-rag-frontend"
echo "  • Stop frontend: docker stop hebrew-rag-frontend"
echo "  • Restart frontend: docker restart hebrew-rag-frontend"
echo "  • Remove frontend: docker rm hebrew-rag-frontend"
EOF

chmod +x $PACKAGE_NAME/deploy.sh

# Create README
print_status "Creating README..."
cat > $PACKAGE_NAME/README.md << 'EOF'
# Hebrew RAG Frontend Package

This package contains the frontend Docker image and deployment script for the Hebrew RAG system.

## Contents

- `hebrew-rag-frontend.tar.gz` - Docker image for Linux AMD64
- `deploy.sh` - Deployment script
- `README.md` - This file

## Requirements

- Docker installed and running
- Backend service running on port 8000

## Deployment

1. Extract the package:
   ```bash
   tar -xzf hebrew-rag-frontend-package.tar.gz
   cd hebrew-rag-frontend-package
   ```

2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

3. Access the frontend:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

## Architecture

The frontend container includes:
- Nginx web server
- Vue.js application
- API proxy to backend
- CORS handling
- Static file serving

## Troubleshooting

- Check if Docker is running: `docker info`
- Check if backend is running: `curl http://localhost:8000/api/v1/health`
- View frontend logs: `docker logs hebrew-rag-frontend`
- Check container status: `docker ps`

## Management

- Stop: `docker stop hebrew-rag-frontend`
- Start: `docker start hebrew-rag-frontend`
- Restart: `docker restart hebrew-rag-frontend`
- Remove: `docker rm hebrew-rag-frontend`
EOF

# Create package info
print_status "Creating package info..."
cat > $PACKAGE_NAME/PACKAGE_INFO.txt << EOF
Hebrew RAG Frontend Package
==========================

Build Date: $(date)
Architecture: Linux AMD64
Image: hebrew-rag-frontend:linux-amd64
Size: $(du -h hebrew-rag-frontend.tar.gz | cut -f1)

Contents:
- Docker image (gzipped)
- Deployment script
- README
- Package info

Built on: $(uname -s) $(uname -m)
Target: Linux AMD64
EOF

cd ..

# Create final compressed package
print_status "Creating final compressed package..."
tar -czf ${PACKAGE_NAME}.tar.gz $PACKAGE_NAME

# Clean up
print_status "Cleaning up..."
rm -rf $PACKAGE_NAME

print_success "Frontend package created successfully!"
echo ""
echo "📦 Package: ${PACKAGE_NAME}.tar.gz"
echo "📏 Size: $(du -h ${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "🚀 To deploy on Linux:"
echo "  1. Copy ${PACKAGE_NAME}.tar.gz to your Linux machine"
echo "  2. Extract: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "  3. Deploy: cd hebrew-rag-frontend-package && ./deploy.sh"
echo ""
echo "✅ Package is ready for Linux deployment!" 