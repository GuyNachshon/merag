#!/bin/bash

# Test script to verify Docker image architecture

echo "Testing Docker image architecture..."

# Check if image exists
if ! docker images | grep -q "hebrew-rag"; then
    echo "Image not found. Building with Linux AMD64 platform..."
    docker build --platform linux/amd64 -t hebrew-rag:latest .
fi

# Check image architecture
echo "Image architecture:"
docker inspect hebrew-rag:latest | grep -A 5 "Architecture"

# Test running a simple command to verify compatibility
echo "Testing container compatibility..."
docker run --rm hebrew-rag:latest uname -m

echo "Architecture test completed!" 