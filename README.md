# Hebrew Agentic RAG System

A local agentic RAG (Retrieval-Augmented Generation) system optimized for Hebrew documents with OCR support, built using modern AI technologies.

## 🌟 Features

- **Hebrew-First Design**: Optimized for Hebrew text processing and generation
- **Multi-Format Support**: PDF, DOCX, images with OCR capabilities
- **Advanced OCR**: dots.ocr model with Tesseract fallback
- **Agentic Architecture**: Using Agno (formerly Phidata) framework
- **Local Processing**: Complete privacy - all processing happens locally
- **Streaming Responses**: Real-time response generation
- **Vue.js Frontend**: Modern, responsive user interface
- **Flexible LLM Support**: Multiple model options including Aya-Expanse, Gemma, Mistral
- **Periodic Indexing**: Automatic file monitoring and indexing from watch directory

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue.js UI     │    │   FastAPI       │    │   Ollama LLM    │
│   Frontend      │────│   Backend       │────│   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
            ┌─────────────────┐  ┌─────────────────┐
            │   Qdrant        │  │   dots.ocr      │
            │   Vector Store  │  │   OCR Service   │
            └─────────────────┘  └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with pip
2. **Node.js 16+** with npm (for frontend)
3. **Ollama** - Install from [ollama.ai](https://ollama.ai)

### Backend Setup

1. **Clone and navigate**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

4. **Pull your chosen LLM**:
   ```bash
   # Example for Aya-Expanse (default)
   ollama pull CohereLabs/aya-expanse-32b
   
   # Or other options:
   # ollama pull google/gemma-3-27b-pt
   # ollama pull mistralai/Mistral-Large-Instruct-2407
   ```

5. **Start the backend**:
   ```bash
   python start.py
   ```

### Frontend Setup

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure API endpoint** (if needed):
   ```bash
   # Create .env.local
   echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env.local
   ```

4. **Start the frontend**:
   ```bash
   npm run dev
   ```

### Usage

1. **Access the application**: Open http://localhost:5173
2. **Upload documents**: Support for PDF, DOCX, images
3. **Ask questions**: Query your documents in Hebrew
4. **Get intelligent responses**: Powered by your local LLM

### Periodic Indexing

The system automatically monitors the `./storage/watch` directory for new files:

1. **Add files to watch directory**: Copy documents to `./storage/watch/`
2. **Automatic processing**: Files are processed every 30 seconds
3. **Query processed documents**: Use the normal query interface
4. **Monitor status**: Check `/api/v1/indexer/status` for processing status

See [PERIODIC_INDEXING.md](PERIODIC_INDEXING.md) for detailed documentation.

## 📁 Project Structure

```
merag/
├── backend/                 # Python FastAPI backend
│   ├── api/                # API endpoints
│   ├── config/             # Configuration management
│   ├── models/             # Pydantic models
│   ├── services/           # Core business logic
│   │   ├── ocr_service.py     # OCR processing
│   │   ├── llm_service.py     # LLM integration
│   │   ├── vector_store_service.py  # Vector storage
│   │   ├── document_processor.py   # Document processing
│   │   └── rag_agent.py       # Agentic RAG system
│   ├── storage/            # Data storage
│   ├── main.py            # FastAPI application
│   └── start.py           # Startup script
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── services/      # API service
│   │   ├── stores/        # Pinia state management
│   │   └── views/         # Page views
│   └── package.json
└── README.md              # This file
```

## ⚙️ Configuration

### LLM Models

Choose from these Hebrew-capable models in your `.env` file:

- `CohereLabs/aya-expanse-32b` (Recommended for Hebrew)
- `google/gemma-3-27b-pt`
- `openai/gpt-oss-20b`
- `ai21labs/AI21-Jamba-Large-1.6`
- `mistralai/Mistral-Large-Instruct-2407`

### Key Settings

```bash
# LLM Configuration
LLM_MODEL=openai/gpt-oss-20b
OLLAMA_HOST=http://localhost:11434

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=100

# OCR Configuration
DOTS_OCR_MODEL=rednote-hilab/dots.ocr
TESSERACT_LANG=heb+eng

# Periodic Indexing Configuration
WATCH_DIRECTORY=./storage/watch
SCAN_INTERVAL_SECONDS=30
ENABLE_PERIODIC_INDEXING=true
```

## 📊 API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload documents
- `GET /api/v1/documents/stats` - Get document statistics
- `DELETE /api/v1/documents/clear` - Clear all documents

### Periodic Indexing
- `GET /api/v1/indexer/status` - Get indexer status
- `POST /api/v1/indexer/scan` - Force immediate directory scan
- `POST /api/v1/indexer/start` - Start periodic indexer
- `POST /api/v1/indexer/stop` - Stop periodic indexer

### Query System
- `POST /api/v1/query` - Query documents
- `POST /api/v1/query/stream` - Streaming query

### System
- `GET /api/v1/health` - Health check
- `GET /docs` - API documentation

## 🔧 Development

### Running in Development Mode

Backend with auto-reload:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend with hot reload:
```bash
cd frontend
npm run dev
```

### Testing

```bash
cd backend
pytest
```

## 🐛 Troubleshooting

### Common Issues

1. **Ollama not accessible**
   - Ensure Ollama is running: `ollama serve`
   - Check the host/port in your `.env` file

2. **OCR not working**
   - Install Tesseract: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Ubuntu)
   - Install Hebrew language pack: `brew install tesseract-lang` (macOS)

3. **Out of memory**
   - Use a smaller LLM model
   - Reduce `CHUNK_SIZE` in configuration

4. **Frontend can't connect to backend**
   - Check CORS settings in backend configuration
   - Verify API URL in frontend environment variables

### Logs

Backend logs are displayed in the console. For more verbose logging:

```bash
export LOG_LEVEL=DEBUG
python start.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [dots.ocr](https://huggingface.co/rednote-hilab/dots.ocr) for multilingual OCR
- [Agno](https://github.com/agno-ai/agno) for the agentic framework
- [Qdrant](https://qdrant.tech/) for vector search
- [Ollama](https://ollama.ai/) for local LLM hosting
- The open-source AI community for Hebrew language models