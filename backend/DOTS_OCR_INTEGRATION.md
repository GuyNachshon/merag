# Dots.OCR Integration

This document describes the integration of the [dots.ocr](https://huggingface.co/rednote-hilab/dots.ocr) model into the Hebrew RAG system.

## Overview

Dots.OCR is a powerful, multilingual document parser that unifies layout detection and content recognition within a single vision-language model. It achieves state-of-the-art performance for text, tables, and reading order while maintaining good multilingual support.

## Features

- **Multilingual Support**: Robust parsing capabilities for low-resource languages including Hebrew
- **Layout Detection**: Identifies document elements like text, tables, formulas, images, etc.
- **Content Recognition**: Extracts text with proper formatting (Markdown, HTML, LaTeX)
- **Reading Order**: Maintains proper document reading order
- **Unified Architecture**: Single model handles multiple tasks through prompt engineering

## Installation

The required dependencies are automatically included in `requirements.txt`:

```bash
pip install transformers>=4.40.0 torch>=2.0.0 qwen-vl-utils>=0.1.0 accelerate>=0.20.0
```

## Configuration

The dots.ocr model is configured in `config/settings.py`:

```python
dots_ocr_model: str = "rednote-hilab/dots.ocr"
```

## Usage

### Basic OCR Processing

```python
from services.ocr_service import ocr_service

# Initialize the service
await ocr_service.initialize()

# Process an image
result = await ocr_service.extract_text_from_image(
    "path/to/image.png", 
    task_type="full"
)

# Process a PDF
result = await ocr_service.extract_text_from_pdf(
    "path/to/document.pdf", 
    task_type="full"
)
```

### Task Types

The OCR service supports three task types:

1. **`full`** (default): Complete layout detection and text extraction
   - Returns structured JSON with bounding boxes, categories, and text
   - Formats text appropriately (Markdown, HTML, LaTeX)

2. **`layout_only`**: Layout detection only
   - Returns bounding boxes and categories without text content
   - Useful for document structure analysis

3. **`ocr_only`**: Text extraction only
   - Returns plain text without layout information
   - Excludes page headers and footers

### API Endpoints

The integration provides several REST API endpoints:

#### Process Image
```http
POST /api/v1/ocr/process-image
Content-Type: multipart/form-data

file: [image file]
task_type: full
```

#### Process PDF
```http
POST /api/v1/ocr/process-pdf
Content-Type: multipart/form-data

file: [pdf file]
task_type: full
```

#### Get OCR Status
```http
GET /api/v1/ocr/status
```

### Response Format

Successful OCR responses include:

```json
{
  "success": true,
  "text": "extracted text content",
  "method": "dots.ocr",
  "task_type": "full",
  "parsed": {
    // Structured layout data (for full/layout_only tasks)
  },
  "total_pages": 1,
  "pages": [
    // Per-page results (for PDF processing)
  ]
}
```

## Integration with Document Processing

The dots.ocr service is **only used during document processing/indexing**, not for user interaction:

1. **Document Upload**: When users upload images or PDFs, dots.ocr extracts text and layout information
2. **Text Processing**: Extracted text is processed and stored in the vector database
3. **User Queries**: User interactions use the regular LLM (Ollama) with the processed text from the vector store
4. **Fallback**: Tesseract OCR is used as a fallback if dots.ocr fails

**Architecture Flow**:
```
Document Upload → Dots.OCR → Text Extraction → Vector Store → User Queries → LLM Response
```

**Key Point**: Dots.ocr is purely a document processing tool. User interactions are handled by the configured LLM (e.g., Aya-Expanse, Gemma, etc.) through the normal RAG pipeline.

## Performance Considerations

- **Model Size**: The dots.ocr model is ~1.7B parameters
- **Memory Usage**: Requires significant GPU memory (recommended: 8GB+ VRAM)
- **Processing Speed**: Faster than many larger models but slower than Tesseract
- **Quality**: Significantly better than Tesseract for complex documents

## Limitations

- **Complex Tables**: May struggle with very complex table structures
- **Formulas**: Formula recognition is good but not perfect
- **Pictures**: Image content within documents is not parsed
- **High Resolution**: Performance may degrade with very high-resolution images

## Testing

Run the test script to verify the integration:

```bash
cd backend
python test_dots_ocr.py
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**: Reduce batch size or use CPU processing
2. **Model Download Issues**: Check internet connection and HuggingFace access
3. **Import Errors**: Ensure all dependencies are installed correctly

### Fallback Behavior

If dots.ocr fails, the system automatically falls back to Tesseract OCR:

```python
# Force fallback to Tesseract
result = await ocr_service.extract_text_from_image(
    "image.png", 
    use_fallback=True
)
```

## References

- [Dots.OCR Model](https://huggingface.co/rednote-hilab/dots.ocr)
- [Dots.OCR GitHub](https://github.com/rednote-hilab/dots.ocr)
- [OmniDocBench Benchmark](https://github.com/opendatalab/OmniDocBench) 