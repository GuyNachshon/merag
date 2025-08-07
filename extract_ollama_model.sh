#!/bin/bash

# Extract Ollama Model for Airgapped Deployment
# This script extracts the gpt-oss:20b model from local Ollama installation

set -e

echo "🔍 Extracting Ollama model for airgapped deployment..."
echo "======================================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Ollama is installed and running
check_ollama() {
    print_status "Checking Ollama installation..."
    
    if ! command -v ollama &> /dev/null; then
        print_warning "Ollama not found in PATH"
        print_status "Checking common installation locations..."
        
        # Check common Ollama locations
        OLLAMA_PATHS=(
            "/usr/local/bin/ollama"
            "/opt/ollama/bin/ollama"
            "$HOME/.local/bin/ollama"
            "/usr/bin/ollama"
        )
        
        for path in "${OLLAMA_PATHS[@]}"; do
            if [ -f "$path" ]; then
                OLLAMA_BIN="$path"
                print_success "Found Ollama at: $OLLAMA_BIN"
                break
            fi
        done
        
        if [ -z "$OLLAMA_BIN" ]; then
            echo "❌ Ollama not found. Please install Ollama first."
            exit 1
        fi
    else
        OLLAMA_BIN="ollama"
        print_success "Ollama found in PATH"
    fi
}

# Check if model exists
check_model() {
    print_status "Checking if gpt-oss:20b model is available..."
    
    if $OLLAMA_BIN list | grep -q "gpt-oss:20b"; then
        print_success "gpt-oss:20b model found"
        return 0
    else
        print_warning "gpt-oss:20b model not found"
        print_status "Available models:"
        $OLLAMA_BIN list
        echo ""
        read -p "Do you want to pull gpt-oss:20b now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Pulling gpt-oss:20b model (this may take a while)..."
            $OLLAMA_BIN pull gpt-oss:20b
        else
            echo "❌ Model not available. Please pull it first with: ollama pull gpt-oss:20b"
            exit 1
        fi
    fi
}

# Find Ollama data directory
find_ollama_data() {
    print_status "Finding Ollama data directory..."
    
    # Common Ollama data locations
    OLLAMA_DATA_PATHS=(
        "$HOME/.ollama"
        "/root/.ollama"
        "/var/lib/ollama"
        "/opt/ollama"
    )
    
    for path in "${OLLAMA_DATA_PATHS[@]}"; do
        if [ -d "$path" ] && [ -d "$path/models" ]; then
            OLLAMA_DATA="$path"
            print_success "Found Ollama data at: $OLLAMA_DATA"
            break
        fi
    done
    
    if [ -z "$OLLAMA_DATA" ]; then
        echo "❌ Ollama data directory not found"
        echo "Please check where Ollama stores its models"
        exit 1
    fi
}

# Extract the model
extract_model() {
    print_status "Extracting gpt-oss:20b model..."
    
    MODEL_DIR="$OLLAMA_DATA/models"
    TARGET_DIR="ollama-models"
    
    # Create target directory
    mkdir -p "$TARGET_DIR"
    
    # Find the model files - Ollama uses a specific directory structure
    if [ -d "$MODEL_DIR/manifests/registry.ollama.ai/library/gpt-oss" ]; then
        print_status "Found gpt-oss model in Ollama manifests"
        
        # Create the target directory structure
        mkdir -p "$TARGET_DIR/manifests/registry.ollama.ai/library"
        
        # Copy the model manifest
        cp -r "$MODEL_DIR/manifests/registry.ollama.ai/library/gpt-oss" "$TARGET_DIR/manifests/registry.ollama.ai/library/"
        
        # Copy the blobs directory (contains the actual model files)
        if [ -d "$MODEL_DIR/blobs" ]; then
            cp -r "$MODEL_DIR/blobs" "$TARGET_DIR/"
            print_success "Model extracted to: $TARGET_DIR/"
        else
            echo "❌ Blobs directory not found"
            exit 1
        fi
    else
        print_warning "Model directory not found in expected location"
        print_status "Available models in $MODEL_DIR/manifests/registry.ollama.ai/library:"
        ls -la "$MODEL_DIR/manifests/registry.ollama.ai/library/"
        echo ""
        read -p "Enter the exact model directory name: " MODEL_NAME
        if [ -d "$MODEL_DIR/manifests/registry.ollama.ai/library/$MODEL_NAME" ]; then
            mkdir -p "$TARGET_DIR/manifests/registry.ollama.ai/library"
            cp -r "$MODEL_DIR/manifests/registry.ollama.ai/library/$MODEL_NAME" "$TARGET_DIR/manifests/registry.ollama.ai/library/"
            cp -r "$MODEL_DIR/blobs" "$TARGET_DIR/"
            print_success "Model extracted to: $TARGET_DIR/"
        else
            echo "❌ Model directory not found: $MODEL_DIR/manifests/registry.ollama.ai/library/$MODEL_NAME"
            exit 1
        fi
    fi
}

# Create load script
create_load_script() {
    print_status "Creating model load script..."
    
    cat > "$TARGET_DIR/load_model.sh" << 'EOF'
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

    chmod +x "$TARGET_DIR/load_model.sh"
    print_success "Load script created: $TARGET_DIR/load_model.sh"
}

# Create package info
create_package_info() {
    print_status "Creating package information..."
    
    cat > "$TARGET_DIR/PACKAGE_INFO.txt" << 'EOF'
Ollama Model Package for Hebrew Agentic RAG
==========================================

Package Contents:
- gpt-oss:20b model files
- load_model.sh: Script to load the model
- PACKAGE_INFO.txt: This file

Model Details:
- Name: gpt-oss:20b
- Size: ~40GB (uncompressed)
- Type: Large Language Model
- Purpose: Hebrew text generation and processing

Installation:
1. Extract this package on the target system
2. Run: ./load_model.sh
3. Verify with: ollama list

Requirements:
- Ollama installed on target system
- ~40GB free disk space
- No internet connection required

Usage:
After loading, the model will be available as "gpt-oss:20b"
in the Hebrew Agentic RAG system.
EOF

    print_success "Package info created: $TARGET_DIR/PACKAGE_INFO.txt"
}

# Compress the package
compress_package() {
    print_status "Compressing Ollama model package..."
    
    PACKAGE_NAME="ollama-gpt-oss-model.tar.gz"
    
    if tar -czf "$PACKAGE_NAME" "$TARGET_DIR/"; then
        PACKAGE_SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)
        print_success "Package created: $PACKAGE_NAME ($PACKAGE_SIZE)"
    else
        echo "❌ Failed to create package"
        exit 1
    fi
}

# Show summary
show_summary() {
    echo ""
    echo "🎉 Ollama Model Extraction Complete!"
    echo "===================================="
    echo ""
    echo "📦 Generated Files:"
    echo "  • $TARGET_DIR/ (extracted model files)"
    echo "  • $PACKAGE_NAME (compressed package)"
    echo ""
    echo "📋 Package Contents:"
    echo "  • gpt-oss:20b model files"
    echo "  • load_model.sh (installation script)"
    echo "  • PACKAGE_INFO.txt (documentation)"
    echo ""
    echo "🚀 Deployment Instructions:"
    echo "  1. Transfer $PACKAGE_NAME to target system"
    echo "  2. Extract: tar -xzf $PACKAGE_NAME"
    echo "  3. Load model: cd ollama-models && ./load_model.sh"
    echo "  4. Verify: ollama list"
    echo ""
    echo "📖 For complete airgapped deployment:"
    echo "  • Main package: hebrew-rag-airgapped-package.tar.gz"
    echo "  • Ollama model: $PACKAGE_NAME"
    echo ""
}

# Main execution
main() {
    check_ollama
    check_model
    find_ollama_data
    extract_model
    create_load_script
    create_package_info
    compress_package
    show_summary
}

# Run main function
main "$@" 