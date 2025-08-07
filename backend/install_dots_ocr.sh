#!/bin/bash

# Dots.OCR Installation Script
# This script installs the required dependencies for dots.ocr

set -e

echo "🚀 Installing Dots.OCR dependencies..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

echo "✅ Python and pip are available"

# Install PyTorch first (with CUDA support if available)
echo "📦 Installing PyTorch..."
if command -v nvidia-smi &> /dev/null; then
    echo "🔍 CUDA detected, installing PyTorch with CUDA support..."
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "🔍 No CUDA detected, installing CPU-only PyTorch..."
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install other dependencies
echo "📦 Installing other dependencies..."
pip3 install transformers>=4.40.0
pip3 install qwen-vl-utils>=0.1.0
pip3 install accelerate>=0.20.0

# Install the rest of the requirements
echo "📦 Installing remaining requirements..."
pip3 install -r requirements.txt

echo "✅ Dots.OCR dependencies installed successfully!"

# Test the installation
echo "🧪 Testing installation..."
python3 -c "
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoProcessor
    from qwen_vl_utils import process_vision_info
    print('✅ All imports successful')
    print(f'PyTorch version: {torch.__version__}')
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'CUDA device count: {torch.cuda.device_count()}')
        print(f'CUDA device name: {torch.cuda.get_device_name(0)}')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Start the backend: python3 start.py"
echo "2. Test the integration: python3 test_dots_ocr.py"
echo "3. Check the API: curl http://localhost:8000/api/v1/ocr/status"
echo ""
echo "For more information, see: DOTS_OCR_INTEGRATION.md" 