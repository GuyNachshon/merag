#!/bin/bash

# Hebrew RAG System - Data Management Script
# This script helps manage data persistence, backups, and updates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
STORAGE_DIR="./storage"
BACKUP_DIR="./backups"
WATCH_DIR="$STORAGE_DIR/watch"
UPLOADS_DIR="$STORAGE_DIR/uploads"
QDRANT_DIR="$STORAGE_DIR/qdrant"
VECTOR_DB_DIR="$STORAGE_DIR/vector_db"

# Create necessary directories
create_directories() {
    print_status "Creating storage directories..."
    mkdir -p "$STORAGE_DIR"/{uploads,qdrant,vector_db,watch,fastembed_cache}
    mkdir -p "$BACKUP_DIR"
    print_success "Storage directories created"
}

# Copy files to watch directory for automatic processing
copy_to_watch() {
    if [ $# -eq 0 ]; then
        print_error "Usage: $0 copy-to-watch <source_directory>"
        exit 1
    fi
    
    SOURCE_DIR="$1"
    if [ ! -d "$SOURCE_DIR" ]; then
        print_error "Source directory not found: $SOURCE_DIR"
        exit 1
    fi
    
    print_status "Copying files from $SOURCE_DIR to watch directory..."
    
    # Copy supported file types
    find "$SOURCE_DIR" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.txt" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -exec cp {} "$WATCH_DIR/" \;
    
    FILE_COUNT=$(find "$WATCH_DIR" -type f | wc -l)
    print_success "Copied files to watch directory. Total files: $FILE_COUNT"
    print_status "Files will be automatically processed by the periodic indexer"
}

# Create backup of all data
create_backup() {
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    print_status "Creating backup: $BACKUP_NAME"
    
    # Create backup directory
    mkdir -p "$BACKUP_PATH"
    
    # Backup storage data
    if [ -d "$STORAGE_DIR" ]; then
        print_status "Backing up storage data..."
        tar -czf "$BACKUP_PATH/storage.tar.gz" -C "$(dirname "$STORAGE_DIR")" "$(basename "$STORAGE_DIR")"
        print_success "Storage backup created: $BACKUP_PATH/storage.tar.gz"
    fi
    
    # Backup Ollama models if available
    if [ -d "$HOME/.ollama/models" ]; then
        print_status "Backing up Ollama models..."
        tar -czf "$BACKUP_PATH/ollama-models.tar.gz" -C "$HOME/.ollama" models
        print_success "Ollama models backup created: $BACKUP_PATH/ollama-models.tar.gz"
    fi
    
    # Create backup info
    cat > "$BACKUP_PATH/backup-info.txt" << EOF
Hebrew RAG System Backup
=======================

Backup created: $(date)
Backup name: $BACKUP_NAME

Contents:
- storage.tar.gz: All storage data (uploads, vector DB, etc.)
- ollama-models.tar.gz: Ollama model files (if available)

To restore:
1. Stop the system: docker stop hebrew-rag-system
2. Extract storage: tar -xzf storage.tar.gz
3. Extract models: tar -xzf ollama-models.tar.gz (if available)
4. Restart: docker start hebrew-rag-system
EOF
    
    print_success "Backup completed: $BACKUP_PATH"
    print_status "Backup info saved to: $BACKUP_PATH/backup-info.txt"
}

# Restore from backup
restore_backup() {
    if [ $# -eq 0 ]; then
        print_error "Usage: $0 restore <backup_name>"
        print_status "Available backups:"
        ls -la "$BACKUP_DIR" | grep "^d" | awk '{print $NF}' | grep -v "^\.$"
        exit 1
    fi
    
    BACKUP_NAME="$1"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        print_error "Backup not found: $BACKUP_NAME"
        exit 1
    fi
    
    print_warning "This will overwrite current data. Are you sure? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Restore cancelled"
        exit 0
    fi
    
    print_status "Restoring from backup: $BACKUP_NAME"
    
    # Stop the system
    print_status "Stopping Hebrew RAG system..."
    docker stop hebrew-rag-system 2>/dev/null || true
    
    # Restore storage data
    if [ -f "$BACKUP_PATH/storage.tar.gz" ]; then
        print_status "Restoring storage data..."
        tar -xzf "$BACKUP_PATH/storage.tar.gz" -C "$(dirname "$STORAGE_DIR")"
        print_success "Storage data restored"
    fi
    
    # Restore Ollama models
    if [ -f "$BACKUP_PATH/ollama-models.tar.gz" ]; then
        print_status "Restoring Ollama models..."
        mkdir -p "$HOME/.ollama"
        tar -xzf "$BACKUP_PATH/ollama-models.tar.gz" -C "$HOME/.ollama"
        print_success "Ollama models restored"
    fi
    
    # Start the system
    print_status "Starting Hebrew RAG system..."
    docker start hebrew-rag-system
    
    print_success "Restore completed successfully"
}

# Show system status
show_status() {
    print_status "Hebrew RAG System Status"
    echo "============================"
    
    # Container status
    if docker ps | grep -q hebrew-rag-system; then
        print_success "Container: Running"
    else
        print_error "Container: Not running"
    fi
    
    # Storage usage
    echo ""
    print_status "Storage Usage:"
    if [ -d "$STORAGE_DIR" ]; then
        du -sh "$STORAGE_DIR"/* 2>/dev/null || true
    else
        print_warning "Storage directory not found"
    fi
    
    # File counts
    echo ""
    print_status "File Counts:"
    if [ -d "$UPLOADS_DIR" ]; then
        UPLOAD_COUNT=$(find "$UPLOADS_DIR" -type f | wc -l)
        echo "  Uploads: $UPLOAD_COUNT files"
    fi
    
    if [ -d "$WATCH_DIR" ]; then
        WATCH_COUNT=$(find "$WATCH_DIR" -type f | wc -l)
        echo "  Watch directory: $WATCH_COUNT files"
    fi
    
    # Backups
    echo ""
    print_status "Available Backups:"
    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(find "$BACKUP_DIR" -type d | wc -l)
        if [ "$BACKUP_COUNT" -gt 1 ]; then
            ls -la "$BACKUP_DIR" | grep "^d" | awk '{print $NF}' | grep -v "^\.$"
        else
            echo "  No backups found"
        fi
    else
        echo "  Backup directory not found"
    fi
}

# Clean up old files
cleanup() {
    print_status "Cleaning up old files..."
    
    # Clean watch directory (processed files)
    if [ -d "$WATCH_DIR" ]; then
        WATCH_COUNT=$(find "$WATCH_DIR" -type f | wc -l)
        if [ "$WATCH_COUNT" -gt 0 ]; then
            print_status "Found $WATCH_COUNT files in watch directory"
            print_warning "These files should be processed automatically. Check system logs if they're not being processed."
        fi
    fi
    
    # Clean old backups (keep last 5)
    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(find "$BACKUP_DIR" -type d | wc -l)
        if [ "$BACKUP_COUNT" -gt 6 ]; then  # 5 + 1 for the directory itself
            print_status "Cleaning old backups (keeping last 5)..."
            ls -t "$BACKUP_DIR" | tail -n +6 | xargs -I {} rm -rf "$BACKUP_DIR/{}"
            print_success "Old backups cleaned"
        fi
    fi
    
    print_success "Cleanup completed"
}

# Show usage
show_usage() {
    echo "Hebrew RAG System - Data Management Script"
    echo "=========================================="
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  init                    - Initialize storage directories"
    echo "  copy-to-watch <dir>     - Copy files to watch directory for processing"
    echo "  backup                  - Create backup of all data"
    echo "  restore <backup_name>   - Restore from backup"
    echo "  status                  - Show system status"
    echo "  cleanup                 - Clean up old files and backups"
    echo "  help                    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 init"
    echo "  $0 copy-to-watch /path/to/documents"
    echo "  $0 backup"
    echo "  $0 restore backup-20240115-143022"
    echo "  $0 status"
}

# Main script logic
case "${1:-help}" in
    init)
        create_directories
        ;;
    copy-to-watch)
        copy_to_watch "$2"
        ;;
    backup)
        create_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac 