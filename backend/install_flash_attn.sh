#!/bin/bash

# Install Flash Attention Script
# This script installs flash-attn for better dots.ocr performance

set -e

echo "⚡ Installing Flash Attention for better performance..."

# Try to install flash-attn
echo "📦 Installing flash-attn..."
if pip install flash-attn>=2.0.0; then
    echo "✅ flash-attn installed successfully"
else
    echo "⚠️  flash-attn installation failed - will use fallback"
    echo "This is normal on some systems. The system will work without it."
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "You can now run the enhanced features test:"
echo "python test_enhanced_features.py" 