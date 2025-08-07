#!/bin/bash

# Fix Dependencies Script
# This script installs missing dependencies for the enhanced features

set -e

echo "🔧 Fixing missing dependencies..."

# Install PyMuPDF
echo "📦 Installing PyMuPDF..."
pip install PyMuPDF==1.23.5

# Install flash-attn (optional, for better performance)
echo "📦 Installing flash-attn (optional)..."
pip install flash-attn>=2.0.0 || echo "⚠️  flash-attn installation failed (will use fallback)"

# Verify installation
echo "✅ Verifying installations..."
python -c "
try:
    import fitz
    print('✅ PyMuPDF installed successfully')
except ImportError as e:
    print(f'❌ PyMuPDF import failed: {e}')
    exit(1)

try:
    import flash_attn
    print('✅ flash-attn installed successfully')
except ImportError:
    print('⚠️  flash-attn not available (will use fallback)')
"

echo ""
echo "🎉 Dependencies fixed!"
echo ""
echo "You can now run the enhanced features test:"
echo "python test_enhanced_features.py" 