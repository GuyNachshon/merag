# Periodic Indexing Feature

The Hebrew RAG system now includes automatic periodic indexing of files from a watched directory. This feature allows you to automatically process and index new documents without manual intervention.

## Overview

The periodic indexer monitors a designated directory (`./storage/watch` by default) for new files and automatically processes them using the same pipeline as manual uploads:

1. **File Detection**: Scans the watch directory every 30 seconds (configurable)
2. **File Processing**: Uses OCR and document processing services
3. **Vector Indexing**: Adds processed documents to the Qdrant vector store
4. **Cleanup**: Removes processed files from the watch directory
5. **Tracking**: Maintains a database of processed files to avoid re-processing

## Configuration

### Environment Variables

Add these to your `.env` file to customize the periodic indexing behavior:

```bash
# Periodic Indexing Configuration
WATCH_DIRECTORY=./storage/watch          # Directory to monitor
SCAN_INTERVAL_SECONDS=30                 # How often to scan (seconds)
ENABLE_PERIODIC_INDEXING=true           # Enable/disable feature
PROCESSED_FILES_DB=./storage/processed_files.json  # Tracking database
```

### Default Settings

- **Watch Directory**: `./storage/watch`
- **Scan Interval**: 30 seconds
- **Enabled**: `true`
- **Supported Formats**: PDF, DOCX, DOC, TXT, PNG, JPG, JPEG

## API Endpoints

### Get Indexer Status
```http
GET /api/v1/indexer/status
```

Response:
```json
{
  "success": true,
  "status": {
    "enabled": true,
    "running": true,
    "watch_directory": "./storage/watch",
    "scan_interval": 30,
    "processed_files_count": 15,
    "last_scan": "2024-01-15T10:30:00Z"
  }
}
```

### Force Immediate Scan
```http
POST /api/v1/indexer/scan
```

Response:
```json
{
  "success": true,
  "message": "Directory scan completed"
}
```

### Start Indexer
```http
POST /api/v1/indexer/start
```

### Stop Indexer
```http
POST /api/v1/indexer/stop
```

## Usage

### 1. Start the Backend

The periodic indexer starts automatically when you start the backend:

```bash
cd backend
python start.py
```

### 2. Add Files to Watch Directory

Simply copy or move files to the watch directory:

```bash
# Copy files to watch directory
cp my_document.pdf ./storage/watch/
cp another_document.docx ./storage/watch/

# Or move files
mv /path/to/documents/* ./storage/watch/
```

### 3. Monitor Processing

Check the logs to see processing status:

```bash
# Check indexer status via API
curl http://localhost:8000/api/v1/indexer/status

# Check document statistics
curl http://localhost:8000/api/v1/documents/stats
```

### 4. Query Processed Documents

Once files are processed, you can query them through the normal API:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "מה יש במסמך החדש?"}'
```

## File Processing Details

### Supported File Types
- **PDF**: Text extraction + OCR for images
- **DOCX/DOC**: Text extraction
- **TXT**: Direct text processing
- **Images**: OCR processing (PNG, JPG, JPEG)

### Processing Pipeline
1. **File Validation**: Check file type and size
2. **Text Extraction**: Extract text from documents
3. **OCR Processing**: For images and PDFs with images
4. **Chunking**: Split into manageable chunks
5. **Embedding**: Generate vector embeddings
6. **Storage**: Add to Qdrant vector store
7. **Cleanup**: Remove original file

### File Tracking

The system maintains a database of processed files to avoid re-processing the same files. The tracking is based on:
- File name
- File modification time
- File size

## Testing

Use the provided test script to verify the functionality:

```bash
cd backend
python test_periodic_indexing.py
```

This script will:
1. Create test files in the watch directory
2. Wait for processing
3. Check the results

## Troubleshooting

### Indexer Not Starting
- Check if `ENABLE_PERIODIC_INDEXING=true` in your `.env`
- Verify the watch directory exists and is writable
- Check logs for initialization errors

### Files Not Being Processed
- Verify file format is supported
- Check file size (max 100MB by default)
- Ensure files are not corrupted
- Check logs for processing errors

### Duplicate Processing
- The system tracks processed files to avoid duplicates
- If you need to re-process a file, delete it from the tracking database
- Or modify the file (change content/size) to trigger re-processing

### Performance Considerations
- Large files may take time to process
- OCR processing is CPU-intensive
- Consider adjusting scan interval for high-volume scenarios
- Monitor disk space (processed files are deleted)

## Advanced Configuration

### Custom Watch Directory
```bash
# Set a custom watch directory
WATCH_DIRECTORY=/path/to/your/documents
```

### Adjust Scan Frequency
```bash
# Scan every 60 seconds instead of 30
SCAN_INTERVAL_SECONDS=60

# Scan every 5 seconds for real-time processing
SCAN_INTERVAL_SECONDS=5
```

### Disable Feature
```bash
# Disable periodic indexing
ENABLE_PERIODIC_INDEXING=false
```

## Integration with Existing Workflow

The periodic indexer works alongside the existing manual upload API:

- **Manual Uploads**: Continue to work as before via `/api/v1/documents/upload`
- **Automatic Indexing**: Processes files from watch directory
- **Unified Storage**: All documents go to the same vector store
- **Consistent Processing**: Same OCR and chunking pipeline

This allows for flexible document ingestion - you can use manual uploads for immediate processing and the watch directory for automated workflows. 