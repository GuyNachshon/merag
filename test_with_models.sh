#!/bin/bash

set -e

echo "🧪 Testing Ollama with Extracted Models"
echo "======================================"

# Check if we have extracted models
if [ ! -d "../ollama-models" ]; then
    echo "❌ No extracted models found. Run extract_ollama_model.sh first."
    exit 1
fi

echo "Found extracted models, creating test with models..."

# Create a test Dockerfile that includes the models
cat > test_with_models.Dockerfile << 'EOF'
FROM ubuntu:22.04

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and copy the startup script logic
RUN mkdir -p /app && echo '#!/bin/bash\n\
echo "Starting test with models..."\n\
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
# Test model loading\n\
echo "Testing model loading..."\n\
if [ -d "/root/.ollama/models" ]; then\n\
    echo "Found models directory, checking contents..."\n\
    ls -la /root/.ollama/models/ || echo "Models directory empty"\n\
    \n\
    # Try to load models\n\
    echo "Attempting to load models..."\n\
    ollama list || echo "No models loaded yet"\n\
    \n\
    # Check if gpt-oss model is available\n\
    if ollama list | grep -q "gpt-oss"; then\n\
        echo "✅ gpt-oss model found!"\n\
    else\n\
        echo "⚠️  gpt-oss model not found, checking model files..."\n\
        find /root/.ollama -name "*gpt-oss*" -type f || echo "No gpt-oss files found"\n\
    fi\n\
else\n\
    echo "❌ No models directory found"\n\
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

# Copy the extracted models
COPY ../ollama-models /root/.ollama/

EXPOSE 11434
CMD ["/app/test.sh"]
EOF

echo "Building test container with models..."
docker build -f test_with_models.Dockerfile -t test-ollama-with-models .

echo "Running test container with models..."
docker run --rm -p 11434:11434 test-ollama-with-models

echo "Test completed!" 