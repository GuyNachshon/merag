#!/bin/bash

# Simple build script for airgapped Docker image

echo "Building airgapped Docker image..."

# Build the image
docker build --platform linux/amd64 -f Dockerfile.airgapped -t hebrew-rag:latest .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "You can now run the container with:"
    echo "  ./run_airgapped.sh start"
else
    echo "❌ Build failed!"
    exit 1
fi 