#!/bin/bash

# Hebrew Agentic RAG - Airgapped Deployment Setup Script
# This script prepares everything needed for airgapped deployment

set -e  # Exit on any error

echo "🚀 Hebrew Agentic RAG - Airgapped Deployment Setup"
echo "=================================================="

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
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check available disk space (need at least 120GB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    available_space_gb=$((available_space / 1024 / 1024))
    
    if [ $available_space_gb -lt 120 ]; then
        print_warning "Available disk space: ${available_space_gb}GB"
        print_warning "Recommended: At least 120GB for the complete package"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "Available disk space: ${available_space_gb}GB"
    fi
    
    print_success "Prerequisites check passed"
}

# Clean up previous builds
cleanup() {
    print_status "Cleaning up previous builds..."
    
    # Remove old Docker images
    docker rmi hebrew-rag:airgapped 2>/dev/null || true
    docker rmi model-test 2>/dev/null || true
    docker rmi frontend-test 2>/dev/null || true
    docker rmi nodejs-test 2>/dev/null || true
    
    # Remove old package files
    rm -f hebrew-rag-airgapped.tar.gz
    rm -rf hebrew-rag-airgapped-package
    
    print_success "Cleanup completed"
}

# Build the Docker image
build_image() {
    print_status "Building Docker image (this may take 30-60 minutes)..."
    print_status "Downloading and caching ML models..."
    print_status "  - FastEmbed: intfloat/multilingual-e5-large (~2GB)"
    print_status "  - Whisper: ivrit-ai/whisper-large-v3 (~3GB)"
    print_status "  - Dots.OCR: rednote-hilab/dots.ocr (~7GB)"
    print_status "  - Ollama: gpt-oss:20b (~40GB)"
    
    if docker build -t hebrew-rag:airgapped .; then
        print_success "Docker image built successfully"
    else
        print_error "Docker build failed"
        exit 1
    fi
}

# Save the Docker image
save_image() {
    print_status "Saving Docker image to tar file..."
    
    if docker save hebrew-rag:airgapped | gzip > hebrew-rag-airgapped.tar.gz; then
        image_size=$(du -h hebrew-rag-airgapped.tar.gz | cut -f1)
        print_success "Docker image saved: hebrew-rag-airgapped.tar.gz (${image_size})"
    else
        print_error "Failed to save Docker image"
        exit 1
    fi
}

# Create deployment package
create_package() {
    print_status "Creating deployment package..."
    
    # Create package directory
    mkdir -p hebrew-rag-airgapped-package
    
    # Copy essential files
    cp hebrew-rag-airgapped.tar.gz hebrew-rag-airgapped-package/
    cp docker-compose.yml hebrew-rag-airgapped-package/
    cp AIRGAPPED_DEPLOYMENT.md hebrew-rag-airgapped-package/
    cp AIRGAPPED_CHECKLIST.md hebrew-rag-airgapped-package/
    
    # Create deployment script
    cat > hebrew-rag-airgapped-package/deploy.sh << 'EOF'
#!/bin/bash

# Hebrew Agentic RAG - Airgapped Deployment Script
# Run this script on the target airgapped system

set -e

echo "🚀 Deploying Hebrew Agentic RAG in airgapped environment..."
echo "=========================================================="

# Check if Docker image exists
if [ ! -f "hebrew-rag-airgapped.tar.gz" ]; then
    echo "❌ Error: hebrew-rag-airgapped.tar.gz not found"
    exit 1
fi

# Load Docker image
echo "📦 Loading Docker image..."
docker load < hebrew-rag-airgapped.tar.gz

# Create necessary directories
echo "📁 Creating storage directories..."
mkdir -p storage/uploads
mkdir -p storage/qdrant
mkdir -p storage/vector_db
mkdir -p storage/watch
mkdir -p storage/fastembed_cache

# Set permissions
chmod 755 storage/uploads
chmod 755 storage/qdrant
chmod 755 storage/vector_db
chmod 755 storage/watch
chmod 755 storage/fastembed_cache

# Start the service
echo "🚀 Starting Hebrew Agentic RAG service..."
docker-compose up -d

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 30

# Check service status
if docker-compose ps | grep -q "Up"; then
    echo "✅ Service is running!"
    echo "🌐 Access the application at: http://localhost:8000"
    echo "📊 Health check: http://localhost:8000/health"
else
    echo "❌ Service failed to start"
    echo "📋 Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "📖 See AIRGAPPED_DEPLOYMENT.md for usage instructions"
EOF

    chmod +x hebrew-rag-airgapped-package/deploy.sh
    
    # Create environment template
    cat > hebrew-rag-airgapped-package/.env.template << 'EOF'
# Hebrew Agentic RAG Environment Configuration
# Copy this file to .env and modify as needed

# Application Settings
APP_NAME=Hebrew Agentic RAG
APP_VERSION=1.0.0
DEBUG=false

# Server Settings
HOST=0.0.0.0
PORT=8000

# Storage Settings
STORAGE_PATH=/app/storage
UPLOAD_PATH=/app/storage/uploads
VECTOR_DB_PATH=/app/storage/vector_db
QDRANT_PATH=/app/storage/qdrant

# Model Settings
FASTEMBED_MODEL=intfloat/multilingual-e5-large
WHISPER_MODEL=ivrit-ai/whisper-large-v3
DOTS_OCR_MODEL=rednote-hilab/dots.ocr
OLLAMA_MODEL=gpt-oss:20b

# Database Settings
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=hebrew_documents

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
EOF

    # Create package info
    cat > hebrew-rag-airgapped-package/PACKAGE_INFO.txt << 'EOF'
Hebrew Agentic RAG - Airgapped Deployment Package
================================================

Package Contents:
- hebrew-rag-airgapped.tar.gz: Docker image with all dependencies
- docker-compose.yml: Service orchestration
- deploy.sh: Deployment script
- AIRGAPPED_DEPLOYMENT.md: Deployment guide
- AIRGAPPED_CHECKLIST.md: Verification checklist
- .env.template: Environment configuration template

System Requirements:
- Linux Ubuntu 22.04 or compatible
- Docker 20.10+
- Docker Compose 2.0+
- 120GB available disk space
- 16GB RAM minimum (32GB recommended)
- No internet connection required

Package Size: ~60GB (compressed)
Uncompressed Size: ~120GB

Models Included:
- FastEmbed: intfloat/multilingual-e5-large (~2GB)
- Whisper: ivrit-ai/whisper-large-v3 (~3GB)
- Dots.OCR: rednote-hilab/dots.ocr (~7GB)
- Ollama: gpt-oss:20b (~40GB)

Quick Start:
1. Copy package to target system
2. Run: ./deploy.sh
3. Access: http://localhost:8000

For detailed instructions, see AIRGAPPED_DEPLOYMENT.md
EOF

    print_success "Deployment package created"
}

# Compress the package
compress_package() {
    print_status "Compressing deployment package..."
    
    if tar -czf hebrew-rag-airgapped-package.tar.gz hebrew-rag-airgapped-package/; then
        package_size=$(du -h hebrew-rag-airgapped-package.tar.gz | cut -f1)
        print_success "Package compressed: hebrew-rag-airgapped-package.tar.gz (${package_size})"
    else
        print_error "Failed to compress package"
        exit 1
    fi
}

# Display final summary
show_summary() {
    echo ""
    echo "🎉 Airgapped Package Creation Complete!"
    echo "======================================"
    echo ""
    echo "📦 Generated Files:"
    echo "  • hebrew-rag-airgapped.tar.gz (Docker image)"
    echo "  • hebrew-rag-airgapped-package/ (Deployment files)"
    echo "  • hebrew-rag-airgapped-package.tar.gz (Complete package)"
    echo ""
    echo "📋 Package Contents:"
    echo "  • Docker image with all dependencies and models"
    echo "  • Deployment script (deploy.sh)"
    echo "  • Docker Compose configuration"
    echo "  • Environment template"
    echo "  • Documentation and guides"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Transfer hebrew-rag-airgapped-package.tar.gz to target system"
    echo "  2. Extract: tar -xzf hebrew-rag-airgapped-package.tar.gz"
    echo "  3. Deploy: cd hebrew-rag-airgapped-package && ./deploy.sh"
    echo ""
    echo "📖 For detailed instructions, see:"
    echo "  • AIRGAPPED_DEPLOYMENT.md"
    echo "  • AIRGAPPED_CHECKLIST.md"
    echo ""
}

# Main execution
main() {
    check_prerequisites
    cleanup
    build_image
    save_image
    create_package
    compress_package
    show_summary
}

# Run main function
main "$@" 