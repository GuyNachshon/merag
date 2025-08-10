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

# Copy files to watch directory for automatic processing (smart copy)
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
    
    print_status "Smart copying files from $SOURCE_DIR to watch directory..."
    
    # Create tracking file for processed files
    TRACKING_FILE="$STORAGE_DIR/copy_tracking.json"
    
    # Initialize tracking file if it doesn't exist
    if [ ! -f "$TRACKING_FILE" ]; then
        echo '{}' > "$TRACKING_FILE"
    fi
    
    # Create temporary tracking file
    TEMP_TRACKING="/tmp/copy_tracking_$$.json"
    echo '{}' > "$TEMP_TRACKING"
    
    # Counters
    NEW_FILES=0
    UPDATED_FILES=0
    SKIPPED_FILES=0
    
    # Find and process supported file types
    while IFS= read -r -d '' file; do
        # Get file info
        FILENAME=$(basename "$file")
        FILE_HASH=$(sha256sum "$file" | cut -d' ' -f1)
        FILE_MODTIME=$(stat -c %Y "$file")
        
        # Check if file exists in tracking
        if jq -e --arg filename "$FILENAME" '.[$filename]' "$TRACKING_FILE" > /dev/null 2>&1; then
            # File exists, check if it changed
            OLD_HASH=$(jq -r --arg filename "$FILENAME" '.[$filename].hash' "$TRACKING_FILE")
            OLD_MODTIME=$(jq -r --arg filename "$FILENAME" '.[$filename].modtime' "$TRACKING_FILE")
            
            if [ "$FILE_HASH" != "$OLD_HASH" ] || [ "$FILE_MODTIME" != "$OLD_MODTIME" ]; then
                # File changed, copy it
                cp "$file" "$WATCH_DIR/"
                echo "  📝 Updated: $FILENAME"
                ((UPDATED_FILES++))
            else
                # File unchanged, skip
                echo "  ⏭️  Skipped (unchanged): $FILENAME"
                ((SKIPPED_FILES++))
            fi
        else
            # New file, copy it
            cp "$file" "$WATCH_DIR/"
            echo "  ➕ New: $FILENAME"
            ((NEW_FILES++))
        fi
        
        # Update tracking
        jq --arg filename "$FILENAME" \
           --arg hash "$FILE_HASH" \
           --arg modtime "$FILE_MODTIME" \
           --arg source "$SOURCE_DIR" \
           --arg timestamp "$(date -Iseconds)" \
           '.[$filename] = {"hash": $hash, "modtime": $modtime, "source": $source, "last_copied": $timestamp}' \
           "$TEMP_TRACKING" > "$TEMP_TRACKING.tmp" && mv "$TEMP_TRACKING.tmp" "$TEMP_TRACKING"
        
    done < <(find "$SOURCE_DIR" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.txt" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -print0)
    
    # Update main tracking file
    jq -s '.[0] * .[1]' "$TRACKING_FILE" "$TEMP_TRACKING" > "$TRACKING_FILE.tmp" && mv "$TRACKING_FILE.tmp" "$TRACKING_FILE"
    
    # Clean up
    rm -f "$TEMP_TRACKING"
    
    # Show summary
    echo ""
    print_success "Smart copy completed!"
    echo "  📊 Summary:"
    echo "    ➕ New files: $NEW_FILES"
    echo "    📝 Updated files: $UPDATED_FILES"
    echo "    ⏭️  Skipped (unchanged): $SKIPPED_FILES"
    echo "    📁 Total files in watch directory: $(find "$WATCH_DIR" -type f | wc -l)"
    echo ""
    print_status "Files will be automatically processed by the periodic indexer"
    print_status "Tracking info saved to: $TRACKING_FILE"
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
    
    # Copy tracking info
    echo ""
    print_status "Copy Tracking:"
    TRACKING_FILE="$STORAGE_DIR/copy_tracking.json"
    if [ -f "$TRACKING_FILE" ]; then
        TRACKED_FILES=$(jq 'length' "$TRACKING_FILE")
        echo "  Tracked files: $TRACKED_FILES"
        echo "  Tracking file: $TRACKING_FILE"
    else
        echo "  No copy tracking found"
    fi
    
    # Scheduled jobs
    echo ""
    print_status "Scheduled Jobs:"
    SCHEDULE_FILE="$STORAGE_DIR/schedule.json"
    if [ -f "$SCHEDULE_FILE" ]; then
        SCHEDULED_COUNT=$(jq 'length' "$SCHEDULE_FILE")
        echo "  Active schedules: $SCHEDULED_COUNT"
        echo "  Schedule file: $SCHEDULE_FILE"
    else
        echo "  No scheduled jobs found"
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

# Show detailed tracking information
show_tracking() {
    TRACKING_FILE="$STORAGE_DIR/copy_tracking.json"
    
    if [ ! -f "$TRACKING_FILE" ]; then
        print_warning "No copy tracking found"
        return
    fi
    
    print_status "Copy Tracking Details"
    echo "========================"
    
    # Show summary
    TOTAL_FILES=$(jq 'length' "$TRACKING_FILE")
    echo "Total tracked files: $TOTAL_FILES"
    echo ""
    
    # Show recent files (last 10)
    echo "Recently copied files:"
    jq -r 'to_entries | sort_by(.value.last_copied) | reverse | .[0:10] | .[] | "  \(.value.last_copied) - \(.key) (from: \(.value.source))"' "$TRACKING_FILE" 2>/dev/null || echo "  No files found"
    
    echo ""
    echo "Source directories:"
    jq -r 'to_entries | group_by(.value.source) | .[] | "  \(.[0].value.source): \(length) files"' "$TRACKING_FILE" 2>/dev/null || echo "  No source directories found"
}

# Schedule automatic copying
schedule_copy() {
    if [ $# -lt 2 ]; then
        print_error "Usage: $0 schedule <source_directory> <interval>"
        print_status "Available intervals: hourly, daily, weekly"
        exit 1
    fi
    
    SOURCE_DIR="$1"
    INTERVAL="$2"
    
    if [ ! -d "$SOURCE_DIR" ]; then
        print_error "Source directory not found: $SOURCE_DIR"
        exit 1
    fi
    
    # Validate interval
    case "$INTERVAL" in
        hourly|daily|weekly)
            ;;
        *)
            print_error "Invalid interval: $INTERVAL"
            print_status "Available intervals: hourly, daily, weekly"
            exit 1
            ;;
    esac
    
    print_status "Scheduling automatic copy from $SOURCE_DIR ($INTERVAL)..."
    
    # Get absolute paths
    SCRIPT_PATH=$(realpath "$0")
    SOURCE_DIR_ABS=$(realpath "$SOURCE_DIR")
    
    # Create cron job entry
    case "$INTERVAL" in
        hourly)
            CRON_SCHEDULE="0 * * * *"
            ;;
        daily)
            CRON_SCHEDULE="0 2 * * *"  # 2 AM daily
            ;;
        weekly)
            CRON_SCHEDULE="0 2 * * 0"  # 2 AM Sunday
            ;;
    esac
    
    # Create cron job
    CRON_JOB="$CRON_SCHEDULE cd $(pwd) && $SCRIPT_PATH copy-to-watch \"$SOURCE_DIR_ABS\" >> logs/cron.log 2>&1"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    # Create logs directory
    mkdir -p logs
    
    # Save schedule info
    SCHEDULE_FILE="$STORAGE_DIR/schedule.json"
    if [ ! -f "$SCHEDULE_FILE" ]; then
        echo '{}' > "$SCHEDULE_FILE"
    fi
    
    # Update schedule info
    jq --arg source "$SOURCE_DIR_ABS" \
       --arg interval "$INTERVAL" \
       --arg schedule "$CRON_SCHEDULE" \
       --arg timestamp "$(date -Iseconds)" \
       '.[$source] = {"interval": $interval, "schedule": $schedule, "created": $timestamp}' \
       "$SCHEDULE_FILE" > "$SCHEDULE_FILE.tmp" && mv "$SCHEDULE_FILE.tmp" "$SCHEDULE_FILE"
    
    print_success "Scheduled automatic copy: $SOURCE_DIR_ABS ($INTERVAL)"
    print_status "Cron job added: $CRON_SCHEDULE"
    print_status "Logs will be written to: logs/cron.log"
    print_status "Schedule info saved to: $SCHEDULE_FILE"
}

# Remove scheduled jobs
unschedule() {
    print_status "Removing scheduled jobs..."
    
    # Get current crontab
    CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")
    
    # Remove our jobs (lines containing the script path)
    SCRIPT_PATH=$(realpath "$0")
    NEW_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "$SCRIPT_PATH" || true)
    
    # Update crontab
    echo "$NEW_CRONTAB" | crontab -
    
    # Clear schedule info
    SCHEDULE_FILE="$STORAGE_DIR/schedule.json"
    if [ -f "$SCHEDULE_FILE" ]; then
        rm "$SCHEDULE_FILE"
    fi
    
    print_success "All scheduled jobs removed"
}

# Show scheduled jobs
show_schedule() {
    print_status "Scheduled Jobs"
    echo "==============="
    
    # Show crontab entries
    CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")
    SCRIPT_PATH=$(realpath "$0")
    
    if echo "$CURRENT_CRONTAB" | grep -q "$SCRIPT_PATH"; then
        echo "Active cron jobs:"
        echo "$CURRENT_CRONTAB" | grep "$SCRIPT_PATH" | while read -r line; do
            echo "  $line"
        done
    else
        echo "No active cron jobs found"
    fi
    
    # Show schedule info
    SCHEDULE_FILE="$STORAGE_DIR/schedule.json"
    if [ -f "$SCHEDULE_FILE" ]; then
        echo ""
        echo "Schedule configuration:"
        jq -r 'to_entries | .[] | "  \(.key): \(.value.interval) (\(.value.schedule))"' "$SCHEDULE_FILE" 2>/dev/null || echo "  No schedule info found"
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
    
    # Clean old log files (keep last 30 days)
    if [ -d "logs" ]; then
        print_status "Cleaning old log files..."
        find logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
        print_success "Old log files cleaned"
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
    echo "  copy-to-watch <dir>     - Smart copy files to watch directory (only new/changed)"
    echo "  backup                  - Create backup of all data"
    echo "  restore <backup_name>   - Restore from backup"
    echo "  status                  - Show system status"
    echo "  tracking                - Show detailed copy tracking information"
    echo "  cleanup                 - Clean up old files and backups"
    echo "  schedule <dir> <interval> - Schedule automatic copying (e.g., schedule /path/to/docs hourly)"
    echo "  unschedule              - Remove scheduled jobs"
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
    tracking)
        show_tracking
        ;;
    schedule)
        schedule_copy "$2" "$3"
        ;;
    unschedule)
        unschedule
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