# Dots.OCR Architecture in Hebrew RAG System

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue.js UI     │    │   FastAPI       │    │   Ollama LLM    │
│   Frontend      │────│   Backend       │────│   (User Queries)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
            ┌─────────────────┐  ┌─────────────────┐
            │   Qdrant        │  │   Document      │
            │   Vector Store  │  │   Processing    │
            └─────────────────┘  └─────────────────┘
                                          │
                                 ┌────────┴────────┐
                                 │                 │
                    ┌─────────────────┐  ┌─────────────────┐
                    │   Dots.OCR      │  │   Tesseract     │
                    │   (Indexing)    │  │   (Fallback)    │
                    └─────────────────┘  └─────────────────┘
```

## Processing Flow

### 1. Document Upload & Indexing
```
User Upload → Document Processor → Dots.OCR → Text Extraction → Vector Store
```

### 2. User Query & Response
```
User Query → RAG Agent → Vector Search → LLM (Ollama) → Response
```

## Key Points

- **Dots.OCR**: Only used during document processing/indexing
- **LLM**: Handles all user interactions (Aya-Expanse, Gemma, etc.)
- **No Direct Interaction**: Users never directly interact with dots.ocr
- **Enhanced Quality**: Better OCR quality improves the indexed content
- **Transparent**: Users get better results without knowing about dots.ocr

## Benefits

1. **Better OCR Quality**: Dots.ocr provides superior text extraction
2. **Layout Preservation**: Tables, formulas, and structure are maintained
3. **Hebrew Support**: Excellent Hebrew text recognition
4. **Seamless Integration**: Users get better results automatically
5. **Fallback System**: Tesseract ensures reliability

## Example Flow

1. User uploads Hebrew document with tables
2. Dots.ocr extracts text and identifies table structure
3. Text is processed and stored in vector database
4. User asks: "מה הנתונים בטבלה הראשונה?"
5. LLM searches vector store and finds the table data
6. LLM responds in Hebrew with the table information 