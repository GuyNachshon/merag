#!/bin/bash

# Hebrew RAG System - Airgapped Docker Runner
# Equivalent to docker-compose.yml but using plain Docker commands

set -e

# Configuration
CONTAINER_NAME="hebrew-rag-system"
IMAGE_NAME="hebrew-rag:latest"
HOST_PORT_BACKEND=8000
HOST_PORT_OLLAMA=11434
CONTAINER_PORT_BACKEND=8000
CONTAINER_PORT_OLLAMA=11434

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if container exists
container_exists() {
    docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Function to check if container is running
container_running() {
    docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"
}

# Function to stop and remove existing container
cleanup_container() {
    if container_exists; then
        print_status "Stopping existing container..."
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        print_status "Removing existing container..."
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
    fi
}

# Function to build the image
build_image() {
    print_status "Building Docker image for Linux architecture (airgapped)..."
    docker build --platform linux/amd64 -f Dockerfile.airgapped -t ${IMAGE_NAME} .
}

# Function to create and run the container
run_container() {
    print_status "Creating and starting container..."
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p ${HOST_PORT_BACKEND}:${CONTAINER_PORT_BACKEND} \
        -p ${HOST_PORT_OLLAMA}:${CONTAINER_PORT_OLLAMA} \
        -v "$(pwd)/storage:/app/storage" \
        -e API_HOST=0.0.0.0 \
        -e API_PORT=8000 \
        -e OLLAMA_HOST=http://localhost:11434 \
        -e LLM_MODEL=gpt-oss:20b \
        -e EMBEDDING_MODEL=intfloat/multilingual-e5-large \
        -e DOTS_OCR_MODEL=rednote-hilab/dots.ocr \
        -e TESSERACT_LANG=heb+eng \
        -e CHUNK_SIZE=1000 \
        -e CHUNK_OVERLAP=200 \
        -e MAX_FILE_SIZE_MB=100 \
        -e WATCH_DIRECTORY=/app/storage/watch \
        -e SCAN_INTERVAL_SECONDS=3600 \
        -e ENABLE_PERIODIC_INDEXING=true \
        -e CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080 \
        ${IMAGE_NAME}
}

# Function to show container status
show_status() {
    if container_running; then
        print_status "Container is running"
        echo "Backend API: http://localhost:${HOST_PORT_BACKEND}"
        echo "Ollama API: http://localhost:${HOST_PORT_OLLAMA}"
        echo ""
        echo "Container logs:"
        docker logs --tail=20 ${CONTAINER_NAME}
    else
        print_warning "Container is not running"
        if container_exists; then
            print_status "Container exists but is stopped"
        else
            print_status "Container does not exist"
        fi
    fi
}

# Function to show logs
show_logs() {
    if container_exists; then
        docker logs -f ${CONTAINER_NAME}
    else
        print_error "Container does not exist"
        exit 1
    fi
}

# Function to stop container
stop_container() {
    if container_running; then
        print_status "Stopping container..."
        docker stop ${CONTAINER_NAME}
    else
        print_warning "Container is not running"
    fi
}

# Function to restart container
restart_container() {
    print_status "Restarting container..."
    stop_container
    sleep 2
    run_container
}

# Function to execute command in container
exec_command() {
    if container_running; then
        docker exec -it ${CONTAINER_NAME} "$@"
    else
        print_error "Container is not running"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "Hebrew RAG System - Airgapped Docker Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     Build the Docker image"
    echo "  start     Start the container (builds if needed)"
    echo "  stop      Stop the container"
    echo "  restart   Restart the container"
    echo "  status    Show container status and logs"
    echo "  logs      Show container logs (follow mode)"
    echo "  exec      Execute command in container"
    echo "  cleanup   Stop and remove container"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start the system"
    echo "  $0 exec bash                # Open shell in container"
    echo "  $0 exec python3 main.py     # Run specific command"
    echo "  $0 logs                     # Follow logs"
}

# Main script logic
case "${1:-start}" in
    build)
        build_image
        ;;
    start)
        if ! docker images | grep -q "${IMAGE_NAME}"; then
            print_warning "Image not found, building first..."
            build_image
        fi
        cleanup_container
        run_container
        print_status "Container started successfully!"
        show_status
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        print_status "Container restarted successfully!"
        show_status
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    exec)
        shift
        exec_command "$@"
        ;;
    cleanup)
        cleanup_container
        print_status "Cleanup completed"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 