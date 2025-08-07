#!/bin/bash

# Simple Flash Attention Installation
echo "⚡ Installing Flash Attention..."

# Try different installation methods
echo "Method 1: Direct pip install..."
if pip install flash-attn --no-build-isolation; then
    echo "✅ Flash attention installed successfully!"
    exit 0
fi

echo "Method 2: With specific version..."
if pip install flash-attn==2.3.6; then
    echo "✅ Flash attention installed successfully!"
    exit 0
fi

echo "Method 3: From source..."
if pip install flash-attn --no-build-isolation --no-cache-dir; then
    echo "✅ Flash attention installed successfully!"
    exit 0
fi

echo "❌ All installation methods failed"
echo "This is normal on some systems. The system will work with Tesseract fallback."
echo ""
echo "To use dots.ocr, you may need to:"
echo "1. Install CUDA toolkit"
echo "2. Install PyTorch with CUDA support"
echo "3. Then install flash-attn" 