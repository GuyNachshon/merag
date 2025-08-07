# dots.ocr Integration Guide

## Overview

This integration adds **dots.ocr** (rednote-hilab/dots.ocr) as the primary document parser for the Hebrew RAG system, with PaddleOCR as a reliable fallback.

### Key Benefits

- **State-of-the-art performance**: Superior layout detection and content recognition
- **Multilingual support**: 100+ languages including Hebrew
- **Unified approach**: Single model for layout + content extraction
- **Structured output**: JSON with spatial relationships + markdown text
- **Graceful fallback**: Automatic fallback to PaddleOCR if needed

## Architecture

```
EnhancedHebrewDocumentProcessor
├── DotsOCRProcessor (Primary)
│   ├── Model: rednote-hilab/dots.ocr (1.7B params)
│   ├── Output: Structured JSON + markdown
│   └── Features: Layout detection, reading order, Hebrew support
├── HebrewDocumentProcessor (Fallback)
│   ├── PaddleOCR for text extraction
│   ├── PDFPlumber for layout preservation
│   └── Hebrew text normalization
└── Shared Features
    ├── Hebrew text processing
    ├── Contextual chunking
    └── Spatial relationship analysis
```

## Installation

1. **Update dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify installation:**
```bash
python test_dots_ocr_integration.py
```

## Usage

### Basic Usage

```python
from hebrew_tools.document_processor import EnhancedHebrewDocumentProcessor

# Initialize processor with dots.ocr enabled
processor = EnhancedHebrewDocumentProcessor(
    use_dots_ocr=True,           # Enable dots.ocr
    ocr_enabled=True,            # Enable PaddleOCR fallback  
    layout_analysis=True,        # Enable layout detection
    visual_extraction=True       # Enable visual element extraction
)

# Process document
result = processor.run("path/to/hebrew_document.pdf")

if result["status"] == "success":
    print(f"Processed with: {result['processor_used']}")
    print(f"Total chunks: {result['total_chunks']}")
    
    # Access chunks
    for chunk in result["chunks"]:
        print(f"Chunk: {chunk['chunk_id']}")
        print(f"Type: {chunk['type']}")
        print(f"Hebrew: {chunk['is_hebrew']}")
        print(f"Content: {chunk['content'][:100]}...")
```

### Advanced Configuration

```python
# Custom model path for airgapped deployment
processor = EnhancedHebrewDocumentProcessor(
    model_path="/path/to/models/ocr",  # Custom model cache location
    use_dots_ocr=True
)

# dots.ocr only (no fallback)
from hebrew_tools.document_processor import DotsOCRProcessor

dots_processor = DotsOCRProcessor(
    model_path="models/ocr",
    use_cache=True
)

result = dots_processor.run(
    document_path="document.pdf",
    output_format="structured"  # or "markdown" or "both"
)
```

## Output Format

### Successful Processing
```python
{
    "status": "success",
    "document_path": "/path/to/document.pdf",
    "processor_used": "dots.ocr",  # or "PaddleOCR"
    "chunks": [
        {
            "chunk_id": "dots_page_0_block_0",
            "type": "text",
            "content": "Hebrew text content...",
            "page_number": 0,
            "bbox": [x0, y0, x1, y1],
            "is_hebrew": true,
            "text_direction": "rtl",
            "confidence": 0.95,
            "processor": "dots.ocr"
        },
        {
            "chunk_id": "dots_page_0_table_0", 
            "type": "table",
            "content": "[[row1_col1, row1_col2], [row2_col1, row2_col2]]",
            "page_number": 0,
            "bbox": [x0, y0, x1, y1],
            "processor": "dots.ocr"
        }
    ],
    "total_chunks": 25,
    "pages": 3
}
```

### Error with Fallback Recommendation
```python
{
    "status": "error",
    "error": "dots.ocr model failed to load",
    "fallback_recommended": true
}
```

## Integration with Existing System

The integration is designed to be **drop-in compatible**:

1. **Agno Tools**: Both processors inherit from `agno.tools.Tool`
2. **Chunking Strategy**: Enhanced chunking preserves existing spatial relationships
3. **Hebrew Processing**: Existing Hebrew normalization and RTL handling preserved
4. **Error Handling**: Graceful degradation to PaddleOCR fallback

### Replace Existing Processor

```python
# Old
from hebrew_tools.document_processor import HebrewDocumentProcessor
processor = HebrewDocumentProcessor()

# New - Drop-in replacement
from hebrew_tools.document_processor import EnhancedHebrewDocumentProcessor  
processor = EnhancedHebrewDocumentProcessor()
```

## Performance Considerations

### Memory Usage
- **dots.ocr**: ~4GB RAM for model loading
- **PaddleOCR**: ~500MB RAM
- **Recommendation**: Use CPU inference for airgapped deployment

### Processing Speed
- **dots.ocr**: ~2-5 seconds per page (CPU)
- **PaddleOCR**: ~1-3 seconds per page (CPU)
- **GPU acceleration** available for dots.ocr

### Model Caching
- Models cached in `models/ocr/` directory
- First run downloads ~3-4GB model files
- Subsequent runs load from cache

## Troubleshooting

### Common Issues

1. **"dots.ocr dependencies not available"**
   ```bash
   pip install torch==2.7.0 torchvision==0.22.0 transformers accelerate
   ```

2. **"Failed to setup dots.ocr model"**
   - Check internet connection for model download
   - Verify disk space (need ~5GB free)
   - Check model directory permissions

3. **"CUDA out of memory"**
   ```python
   # Force CPU inference
   processor = EnhancedHebrewDocumentProcessor()
   # Model will automatically use CPU
   ```

4. **Fallback to PaddleOCR**
   - This is normal and expected behavior
   - Check logs to see why dots.ocr failed
   - System continues working with PaddleOCR

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

processor = EnhancedHebrewDocumentProcessor()
result = processor.run("document.pdf")
# Check logs for detailed processing information
```

## Testing

Run the integration test:

```bash
python test_dots_ocr_integration.py
```

Expected output:
```
✅ dots.ocr dependencies are available
✅ EnhancedHebrewDocumentProcessor initialized
✅ Document processing successful!
🎉 All tests passed! Integration is working correctly.
```

## Deployment Notes

### Airgapped Deployment
1. Pre-download model files on connected machine
2. Copy model cache directory to airgapped system
3. Set custom `model_path` during initialization

### Production Recommendations
- Use persistent model caching
- Monitor memory usage (especially with concurrent processing)
- Implement request queuing for high-volume scenarios
- Consider GPU inference for speed-critical applications

## Model Information

- **Repository**: rednote-hilab/dots.ocr
- **Model Size**: 1.7B parameters (~3.4GB)
- **Languages**: 100+ including Hebrew, Arabic, English
- **Input**: PDF, PNG, JPG, TIFF, BMP
- **Output**: Structured JSON, Markdown, or both
- **License**: Check model repository for latest license terms