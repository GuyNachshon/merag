# Hebrew Agentic RAG - Quick Start Guide

## 🚀 One-Command Setup

### For Build Environment (with internet)
```bash
./setup_airgapped.sh
```

This will:
- ✅ Check prerequisites (Docker, disk space)
- 🐳 Build Docker image with all models (~60GB)
- 📦 Create deployment package
- 🗜️ Compress everything into `hebrew-rag-airgapped-package.tar.gz`

### For Airgapped Environment (no internet)
```bash
# 1. Transfer package to target system
# 2. Extract package
tar -xzf hebrew-rag-airgapped-package.tar.gz
cd hebrew-rag-airgapped-package

# 3. Deploy
./deploy.sh
```

## 📋 What You Get

### Complete System
- **Backend API** (FastAPI) - Document processing, search, chat
- **ML Models** - FastEmbed, Whisper, Dots.OCR, Ollama
- **Vector Database** (Qdrant) - Hebrew-optimized storage
- **Web Interface** - Upload, search, chat interface

### Pre-Downloaded Models
- **FastEmbed**: `intfloat/multilingual-e5-large` (~2GB)
- **Whisper**: `ivrit-ai/whisper-large-v3` (~3GB) 
- **Dots.OCR**: `rednote-hilab/dots.ocr` (~7GB)
- **Ollama**: `gpt-oss:20b` (~40GB)

## 🎯 System Requirements

### Target System
- **OS**: Linux Ubuntu 22.04+
- **Docker**: 20.10+
- **Storage**: 120GB free space
- **RAM**: 16GB+ (32GB recommended)
- **Network**: None required

## 🌐 Access Points

After deployment:
- **Web Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🛠️ Management

```bash
# Start services
docker-compose up -d

# Stop services  
docker-compose down

# View logs
docker-compose logs

# Check status
docker-compose ps
```

## 📖 Full Documentation

- **Deployment Guide**: `AIRGAPPED_DEPLOYMENT.md`
- **Verification Checklist**: `AIRGAPPED_CHECKLIST.md`
- **Package Info**: `PACKAGE_INFO.txt`

## 🔧 Troubleshooting

### Quick Fixes
```bash
# Service won't start
docker-compose logs

# Permission issues
chmod -R 755 storage/

# Memory issues
free -h
```

### Common Issues
- **Port 8000 in use**: Change port in `docker-compose.yml`
- **Low disk space**: Check with `df -h`
- **Memory issues**: Increase RAM or add swap

## 📞 Support

- **Logs**: `docker-compose logs hebrew-rag`
- **Health**: `curl http://localhost:8000/health`
- **Status**: `docker-compose ps`

---

**Note**: This system runs completely offline. All models and dependencies are included in the package. 