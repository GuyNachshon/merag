#!/bin/bash

set -e

echo "🚀 Building Hebrew RAG Airgapped Package"
echo "========================================"

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v ollama &> /dev/null; then
    print_error "Ollama is not installed. Please install Ollama first."
    exit 1
fi

print_success "Prerequisites check passed"

# Create ollama-models directory if it doesn't exist
print_status "Preparing Ollama models..."
if [ ! -d "ollama-models" ]; then
    mkdir -p ollama-models
    print_success "Created ollama-models directory"
fi

# Download Ollama model if not already present
print_status "Checking for gpt-oss:20b model..."
if ! ollama list | grep -q "gpt-oss"; then
    print_status "Downloading gpt-oss:20b model (this may take 10-15 minutes)..."
    ollama pull gpt-oss:20b
    if [ $? -ne 0 ]; then
        print_error "Failed to download gpt-oss:20b model"
        exit 1
    fi
    print_success "gpt-oss:20b model downloaded successfully"
else
    print_success "gpt-oss:20b model already exists"
fi

# Extract Ollama model files
print_status "Extracting Ollama model files..."
OLLAMA_DATA="$HOME/.ollama"
if [ ! -d "$OLLAMA_DATA/models" ]; then
    print_error "Ollama models directory not found at $OLLAMA_DATA/models"
    exit 1
fi

# Copy model files to ollama-models directory
cp -r "$OLLAMA_DATA/models"/* ollama-models/
print_success "Ollama model files extracted to ollama-models/"

# Create load script
print_status "Creating model load script..."
cat > ollama-models/load_model.sh << 'EOF'
#!/bin/bash

# Load Ollama Model in Airgapped Environment
# This script loads the extracted Ollama model

set -e

echo "🚀 Loading Ollama model in airgapped environment..."
echo "=================================================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install Ollama first."
    exit 1
fi

# Find Ollama data directory
OLLAMA_DATA="$HOME/.ollama"
if [ ! -d "$OLLAMA_DATA" ]; then
    echo "❌ Ollama data directory not found at $OLLAMA_DATA"
    exit 1
fi

# Copy model files
echo "📁 Copying model files..."
MODEL_DIR="$OLLAMA_DATA/models"

# Create models directory if it doesn't exist
mkdir -p "$MODEL_DIR"

# Copy the extracted model files
if [ -d "manifests" ] && [ -d "blobs" ]; then
    # Copy manifests
    cp -r manifests "$MODEL_DIR/"
    echo "✅ Manifests copied to: $MODEL_DIR/manifests"
    
    # Copy blobs
    cp -r blobs "$MODEL_DIR/"
    echo "✅ Blobs copied to: $MODEL_DIR/blobs"
else
    echo "❌ Model files not found in current directory"
    echo "Expected: manifests/ and blobs/ directories"
    echo "Available directories:"
    ls -la
    exit 1
fi

# Verify model is loaded
echo "🔍 Verifying model..."
if ollama list | grep -q "gpt-oss"; then
    echo "✅ Model loaded successfully!"
    echo "📋 Available models:"
    ollama list
else
    echo "⚠️  Model not showing in ollama list"
    echo "📋 Current models:"
    ollama list
    echo ""
    echo "💡 You may need to restart Ollama or run: ollama pull gpt-oss:20b"
fi

echo ""
echo "🎉 Model loading completed!"
EOF

chmod +x ollama-models/load_model.sh
print_success "Model load script created"

# Create package info
print_status "Creating package info..."
cat > ollama-models/PACKAGE_INFO.txt << EOF
Ollama Models Package
====================

Package created: $(date)
Model: gpt-oss:20b
Size: $(du -sh ollama-models/ | cut -f1)

Contents:
- manifests/ - Model manifests
- blobs/ - Model binary files
- load_model.sh - Model loading script
- PACKAGE_INFO.txt - This file

To load the model:
1. Copy this directory to your airgapped environment
2. Run: ./load_model.sh
EOF

print_success "Package info created"

# Build the Docker image
print_status "Building Docker image..."
docker build --platform linux/amd64 -f Dockerfile.airgapped -t hebrew-rag-airgapped:latest .

if [ $? -ne 0 ]; then
    print_error "Docker build failed!"
    exit 1
fi

print_success "Docker image built successfully"

# Create the airgapped package
PACKAGE_NAME="hebrew-rag-airgapped-package"
print_status "Creating airgapped package..."

# Remove existing package if it exists
if [ -d "$PACKAGE_NAME" ]; then
    rm -rf "$PACKAGE_NAME"
fi

mkdir -p "$PACKAGE_NAME"

# Save Docker image
print_status "Saving Docker image..."
docker save hebrew-rag-airgapped:latest | gzip > "$PACKAGE_NAME/hebrew-rag-airgapped-package.tar.gz"

if [ $? -ne 0 ]; then
    print_error "Failed to save Docker image!"
    exit 1
fi

print_success "Docker image saved"

# Copy deployment files
print_status "Copying deployment files..."
cp deploy.sh "$PACKAGE_NAME/"
cp README.md "$PACKAGE_NAME/"
cp PACKAGE_INFO.txt "$PACKAGE_NAME/"

# Create package info
cat > "$PACKAGE_NAME/PACKAGE_INFO.txt" << EOF
Hebrew RAG System - Airgapped Package
====================================

Package created: $(date)
Docker image: hebrew-rag-airgapped
Package size: $(du -sh "$PACKAGE_NAME" | cut -f1)

Contents:
- Docker image with all dependencies and models
- Deployment scripts
- Configuration templates
- Documentation

Models included:
- FastEmbed: intfloat/multilingual-e5-large (~2GB)
- Whisper: ivrit-ai/whisper-large-v3 (~3GB)
- Dots.OCR: rednote-hilab/dots.ocr (~7GB)
- Ollama: gpt-oss:20b (~40GB)
- Tesseract: Hebrew + English language packs

Total estimated size: ~60GB

To deploy:
1. Extract this package to your airgapped environment
2. Run: ./deploy.sh
EOF

print_success "Deployment files copied"

# Create final package
print_status "Creating final package..."
tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"

if [ $? -ne 0 ]; then
    print_error "Failed to create final package!"
    exit 1
fi

print_success "Final package created: ${PACKAGE_NAME}.tar.gz"

# Display package info
echo ""
echo "🎉 Airgapped package created successfully!"
echo "=========================================="
echo "Package: ${PACKAGE_NAME}.tar.gz"
echo "Size: $(du -sh "${PACKAGE_NAME}.tar.gz" | cut -f1)"
echo ""
echo "To deploy in airgapped environment:"
echo "1. Copy ${PACKAGE_NAME}.tar.gz to your airgapped system"
echo "2. Extract: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "3. Deploy: cd $PACKAGE_NAME && ./deploy.sh"
echo ""
echo "✅ Build completed successfully!" 