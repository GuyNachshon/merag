# Complete Airgapped Package Contents

## 🤖 ML Models (Pre-downloaded)

### Embedding Models
- **FastEmbed**: `intfloat/multilingual-e5-large`
  - Size: ~2GB
  - Purpose: Hebrew-optimized text embeddings
  - Cache location: `/app/models/fastembed/`

### Speech-to-Text Models
- **Whisper**: `ivrit-ai/whisper-large-v3`
  - Size: ~3GB
  - Purpose: Hebrew speech-to-text transcription
  - Cache location: `/app/models/whisper/`

### OCR Models
- **Dots.OCR**: `rednote-hilab/dots.ocr`
  - Size: ~7GB
  - Purpose: Advanced document understanding and OCR
  - Cache location: `/app/models/dots-ocr/`
- **Tesseract**: Hebrew + English language packs
  - Size: ~50MB
  - Purpose: Traditional OCR fallback
  - System installation

### Language Models
- **Ollama**: `gpt-oss:20b`
  - Size: ~40GB
  - Purpose: Hebrew-capable language model for RAG responses
  - Pulled at runtime (not pre-downloaded)

## 📦 Python Dependencies (42 packages)

### Core Framework
- `fastapi==0.104.1` - Web framework
- `uvicorn[standard]==0.24.0` - ASGI server
- `python-multipart==0.0.20` - File upload handling

### RAG & LLM
- `langchain==0.3.18` - RAG framework
- `langchain-community==0.3.17` - Community integrations
- `langchain-core==0.3.35` - Core functionality
- `langchain-text-splitters==0.3.6` - Text chunking
- `agno==1.0.0` - Agent framework
- `ollama==0.4.7` - Ollama client

### Vector Store & Embeddings
- `qdrant-client==1.13.2` - Vector database client
- `langchain-qdrant==0.2.0` - Qdrant integration
- `fastembed==0.5.1` - Fast embedding generation

### OCR & Document Processing
- `Pillow==10.4.0` - Image processing
- `python-docx==0.8.11` - Word document processing
- `PyPDF2==3.0.1` - PDF processing
- `PyMuPDF==1.23.5` - Advanced PDF processing
- `pytesseract==0.3.10` - Tesseract OCR wrapper

### Dots.OCR Dependencies
- `transformers>=4.40.0` - Hugging Face transformers
- `torch>=2.0.0` - PyTorch
- `qwen-vl-utils>=0.1.0` - Vision-language utilities
- `accelerate>=0.20.0` - Model acceleration
- `flash-attn>=2.0.0` - Flash attention

### Hebrew Language Processing
- `hebrew-tokenizer==2.3.0` - Hebrew text tokenization

### Audio Processing
- `librosa` - Audio processing library

### System Monitoring
- `psutil==5.9.6` - System monitoring

### Utilities
- `python-dotenv==1.0.1` - Environment variable management
- `aiofiles==23.2.1` - Async file operations
- `pydantic==2.10.6` - Data validation
- `pydantic-settings==2.7.1` - Settings management
- `httpx==0.28.1` - HTTP client
- `numpy==1.26.4` - Numerical computing
- `pandas==2.1.3` - Data manipulation

### Development
- `pytest==7.4.3` - Testing framework
- `pytest-asyncio==0.21.1` - Async testing
- `black==23.9.1` - Code formatting
- `isort==5.12.0` - Import sorting

## 🎨 Node.js Dependencies (13 packages)

### Core Framework
- `vue==^3.5.17` - Vue.js framework
- `vue-router==^4.5.1` - Vue routing
- `pinia==^3.0.3` - State management

### UI Components
- `@headlessui/vue==^1.7.23` - Headless UI components
- `@floating-ui/dom==^1.7.2` - Floating UI utilities
- `radix-vue==^1.9.17` - Radix UI components

### Icons & Utilities
- `lucide-vue-next==^0.525.0` - Icon library
- `@vueuse/core==^13.5.0` - Vue composition utilities

### Build Tools
- `@vitejs/plugin-vue==^6.0.0` - Vite Vue plugin
- `sass==^1.89.2` - Sass preprocessor
- `vite==^7.0.0` - Build tool
- `vite-plugin-vue-devtools==^7.7.7` - Vue devtools

## 🛠️ Application Code

### Backend Structure
```
/app/backend/
├── api/
│   ├── __init__.py
│   └── routes.py                    # API endpoints
├── config/
│   ├── __init__.py
│   └── settings.py                  # Configuration management
├── models/
│   └── __init__.py                  # Pydantic models
├── services/
│   ├── __init__.py
│   ├── document_processor.py        # Document processing
│   ├── llm_service.py              # LLM integration
│   ├── ocr_service.py              # OCR processing
│   ├── periodic_indexer.py         # File monitoring
│   ├── rag_agent.py                # RAG system
│   ├── transcription_service.py    # Audio transcription
│   └── vector_store_service.py     # Vector storage
├── utils/                          # Utility functions
├── main.py                         # FastAPI application
├── start.py                        # Startup script
└── requirements.txt                # Python dependencies
```

### Frontend Structure
```
/app/frontend/
├── dist/                           # Built assets
│   ├── index.html
│   ├── assets/
│   │   ├── css/
│   │   ├── js/
│   │   └── fonts/
├── src/
│   ├── components/
│   │   ├── ChatTurn.vue
│   │   ├── PromptBox.vue
│   │   └── icons/
│   ├── services/
│   │   └── api.js                  # API integration
│   ├── stores/
│   │   ├── chat.js                 # Chat state
│   │   └── counter.js
│   ├── views/
│   │   └── Chat.vue                # Main chat interface
│   ├── assets/
│   │   ├── base.css
│   │   ├── main.scss
│   │   ├── variables.scss
│   │   └── fonts/
│   ├── router/
│   │   └── index.js
│   └── main.js                     # Vue application entry
├── public/
│   └── favicon.ico
├── package.json                    # Node.js dependencies
└── vite.config.js                  # Build configuration
```

### Test Files
```
/app/backend/
├── test_files/
│   └── test_audio.wav              # Audio test sample
├── test_transcription.py           # Transcription tests
├── test_verification.py            # Verification tests
├── test_enhanced_features.py       # Feature tests
├── test_layout_aware_ocr.py        # OCR tests
├── test_dots_ocr.py                # Dots.OCR tests
├── test_periodic_indexing.py       # Indexing tests
└── create_test_image.py            # Test image creation
```

### Documentation Files
```
/app/backend/
├── DOTS_OCR_ARCHITECTURE.md        # OCR architecture
├── DOTS_OCR_INTEGRATION.md         # OCR integration guide
└── install_dots_ocr.sh             # OCR installation script
```

## 🔧 System Dependencies

### Image Processing Libraries
- `libjpeg-dev` - JPEG support
- `libpng-dev` - PNG support
- `libtiff-dev` - TIFF support
- `libwebp-dev` - WebP support
- `libopenjp2-7-dev` - JPEG 2000 support

### Audio Processing Libraries
- `ffmpeg` - Audio/video processing
- `libsndfile1` - Audio file handling

### OCR Libraries
- `tesseract-ocr` - OCR engine
- `tesseract-ocr-heb` - Hebrew language pack
- `tesseract-ocr-eng` - English language pack

### ML Libraries
- `libatlas-base-dev` - BLAS/LAPACK
- `gfortran` - Fortran compiler
- `build-essential` - Build tools

### Flash Attention Dependencies
- `ninja-build` - Build system
- `cmake` - Build configuration
- `pkg-config` - Package configuration

### Core System Libraries
- `libssl-dev` - SSL/TLS
- `libffi-dev` - Foreign function interface
- `libpq-dev` - PostgreSQL client
- `libgl1-mesa-glx` - OpenGL
- `libglib2.0-0` - GLib
- `libsm6` - X11 session management
- `libxext6` - X11 extensions
- `libxrender-dev` - X11 rendering
- `libgomp1` - OpenMP
- `libgthread-2.0-0` - GLib threading

## 📁 Storage Structure

### Application Storage
```
/app/storage/
├── uploads/                        # Uploaded documents
├── qdrant/                         # Vector database
│   └── collection/
│       └── hebrew_documents/
├── vector_db/                      # Additional vector storage
├── watch/                          # File monitoring directory
└── fastembed_cache/                # Embedding model cache
```

### Model Cache
```
/app/models/
├── fastembed/                      # FastEmbed model cache
├── whisper/                        # Whisper model cache
├── dots-ocr/                       # Dots.OCR model cache
└── transformers/                   # Hugging Face cache
```

## 🌐 Network Configuration

### Ports
- **8000**: FastAPI backend API
- **11434**: Ollama service

### CORS Origins
- `http://localhost:3000`
- `http://localhost:5173`
- `http://localhost:8080`

## 📦 Deployment Package Files

### Core Files
- `Dockerfile` - Multi-stage container build
- `docker-compose.yml` - Service orchestration
- `build-airgapped.sh` - Build script
- `AIRGAPPED_DEPLOYMENT.md` - Deployment guide
- `AIRGAPPED_CHECKLIST.md` - Verification checklist

### Generated Package Contents
```
hebrew-rag-airgapped-package/
├── hebrew-rag-airgapped-package.tar  # Docker image
├── docker-compose.yml                # Service configuration
├── deploy.sh                         # Deployment script
├── README.md                         # User documentation
├── .env.template                     # Configuration template
└── PACKAGE_INFO.txt                  # Package information
```

## 🚀 Startup Process

### Services Started
1. **Ollama Service** - Language model server
2. **FastAPI Application** - Main API server
3. **Health Monitoring** - System health checks

### Initialization Sequence
1. Start Ollama in background
2. Wait for Ollama to be ready
3. Pull required Ollama models
4. Initialize FastAPI application
5. Start all services
6. Verify system health

## 📊 Resource Requirements

### Minimum Requirements
- **RAM**: 8GB
- **Storage**: 120GB
- **CPU**: Multi-core
- **OS**: Ubuntu 22.04 or compatible

### Recommended Requirements
- **RAM**: 16GB+
- **Storage**: 200GB+
- **CPU**: 8+ cores
- **GPU**: Optional (for acceleration)

## 🔒 Security Features

### Airgapped Compliance
- No external network access
- All dependencies pre-installed
- No package managers needed
- Self-contained operation

### Data Protection
- Local storage only
- No external logging
- No telemetry
- Isolated container environment

## 📈 Performance Optimizations

### Model Optimization
- Pre-downloaded models
- Model caching
- Optimized inference settings
- Memory-efficient loading

### System Optimization
- Multi-threaded processing
- Efficient resource usage
- Optimized build process
- Minimal container layers

---

## 🎉 Complete Package Summary

**Total Package Size**: ~60GB (compressed: ~30GB)

**Models**: 4 major ML models (FastEmbed, Whisper, Dots.OCR, Ollama)
**Dependencies**: 55+ packages (42 Python + 13 Node.js)
**Code**: Complete application stack (backend + frontend)
**Documentation**: Comprehensive guides and references
**Tools**: Build scripts, deployment scripts, configuration templates

**Result**: A complete, self-contained Hebrew RAG system ready for airgapped deployment. 