#!/bin/bash

set -e

echo "🧪 Testing Ollama Installation and Startup"
echo "=========================================="

# Create a minimal test Dockerfile
cat > test_ollama.Dockerfile << 'EOF'
FROM ubuntu:22.04

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and copy the startup script logic
RUN mkdir -p /app && echo '#!/bin/bash\n\
echo "Starting test..."\n\
\n\
# Install Ollama if not already installed\n\
if ! command -v ollama >/dev/null 2>&1; then\n\
    echo "Installing Ollama..."\n\
    curl -fsSL https://ollama.ai/install.sh | sh\n\
    export PATH=$PATH:/usr/local/bin\n\
fi\n\
\n\
# Start Ollama\n\
echo "Starting Ollama..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
sleep 10\n\
echo "Ollama started with PID: $OLLAMA_PID"\n\
\n\
# Test if Ollama is responding\n\
echo "Testing Ollama connection..."\n\
for i in {1..5}; do\n\
    if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then\n\
        echo "✅ Ollama is responding!"\n\
        break\n\
    else\n\
        echo "Attempt $i: Ollama not ready yet..."\n\
        sleep 5\n\
    fi\n\
done\n\
\n\
# Test model loading if models are available\n\
echo "Testing model loading..."\n\
if [ -d "/root/.ollama/models" ]; then\n\
    echo "Found models directory, checking contents..."\n\
    ls -la /root/.ollama/models/ || echo "Models directory empty"\n\
    \n\
    # Try to load models\n\
    echo "Attempting to load models..."\n\
    ollama list || echo "No models loaded yet"\n\
    \n\
    # Test if we can pull a small model\n\
    echo "Testing model pull..."\n\
    ollama pull llama2:7b || echo "Model pull failed"\n\
else\n\
    echo "No models directory found"\n\
fi\n\
\n\
# Show final Ollama info\n\
echo "Final Ollama info:"\n\
ollama list || echo "No models loaded"\n\
\n\
echo "✅ Test completed successfully!"\n\
\n\
# Keep container running for inspection\n\
sleep 30\n\
' > /app/test.sh && chmod +x /app/test.sh

EXPOSE 11434
CMD ["/app/test.sh"]
EOF

echo "Building test container..."
docker build -f test_ollama.Dockerfile -t test-ollama .

echo "Running test container..."
docker run --rm -p 11434:11434 test-ollama

echo "Test completed!" 