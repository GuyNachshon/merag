# Hebrew Agentic RAG - Airgapped Deployment Guide

This guide explains how to deploy the Hebrew Agentic RAG system in an airgapped environment (no internet connection).

## 📋 Overview

The Hebrew Agentic RAG system is packaged as **two separate components**:

### **Main Package** (16GB)
- **Backend API** (FastAPI)
- **ML Models** (FastEmbed, Whisper, Dots.OCR)
- **Vector Database** (Qdrant)
- **All Dependencies** (Python, Node.js, system libraries)

### **Ollama Model Package** (~40GB)
- **LLM Model**: `gpt-oss:20b` for Hebrew text generation
- **Installation Script**: Automated model loading
- **Documentation**: Usage instructions

## 🎯 System Requirements

### Target System Requirements
- **OS**: Linux Ubuntu 22.04 or compatible
- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **Ollama**: Installed and running
- **Storage**: 120GB available disk space
- **RAM**: 16GB minimum (32GB recommended)
- **CPU**: 4+ cores recommended
- **Network**: No internet connection required

### Package Sizes
- **Main Package**: ~16GB (compressed)
- **Ollama Model**: ~40GB (compressed)
- **Total**: ~56GB (compressed)
- **Runtime**: ~120GB (after extraction)

## 🚀 Quick Deployment

### Step 1: Transfer Packages
Copy both packages to your target system:
- `hebrew-rag-airgapped-package.tar.gz` (main system)
- `ollama-gpt-oss-model.tar.gz` (LLM model)

### Step 2: Load Ollama Model
```bash
# Extract Ollama model package
tar -xzf ollama-gpt-oss-model.tar.gz
cd ollama-models

# Load the model
./load_model.sh

# Verify model is loaded
ollama list
```

### Step 3: Deploy Main System
```bash
# Extract main package
tar -xzf hebrew-rag-airgapped-package.tar.gz
cd hebrew-rag-airgapped-package

# Deploy
./deploy.sh
```

### Step 4: Access Application
- **Web Interface**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

## 📦 Package Contents

### Main Package
```
hebrew-rag-airgapped-package/
├── hebrew-rag-airgapped.tar.gz    # Docker image with all dependencies
├── docker-compose.yml             # Service orchestration
├── deploy.sh                      # Automated deployment script
├── AIRGAPPED_DEPLOYMENT.md        # This guide
├── AIRGAPPED_CHECKLIST.md         # Verification checklist
├── .env.template                  # Environment configuration template
└── PACKAGE_INFO.txt              # Package information
```

### Ollama Model Package
```
ollama-models/
├── gpt-oss/                       # Model files (~40GB)
├── load_model.sh                  # Installation script
└── PACKAGE_INFO.txt              # Model information
```

## 🔧 Manual Deployment

### 1. Load Ollama Model
```bash
# Extract model package
tar -xzf ollama-gpt-oss-model.tar.gz
cd ollama-models

# Load model into Ollama
./load_model.sh

# Verify
ollama list | grep gpt-oss
```

### 2. Deploy Main System
```bash
# Load Docker image
docker load < hebrew-rag-airgapped.tar.gz

# Create storage directories
mkdir -p storage/uploads
mkdir -p storage/qdrant
mkdir -p storage/vector_db
mkdir -p storage/watch
mkdir -p storage/fastembed_cache

chmod 755 storage/uploads
chmod 755 storage/qdrant
chmod 755 storage/vector_db
chmod 755 storage/watch
chmod 755 storage/fastembed_cache

# Start services
docker-compose up -d
```

### 3. Verify Deployment
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs

# Test health endpoint
curl http://localhost:8000/health
```

## 🛠️ Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs hebrew-rag

# Follow logs
docker-compose logs -f
```

### Restart Services
```bash
docker-compose restart
```

### Ollama Model Management
```bash
# List available models
ollama list

# Test model
ollama run gpt-oss:20b "שלום עולם"

# Remove model (if needed)
ollama rm gpt-oss:20b
```

## 📊 Monitoring

### Health Checks
- **Application Health**: `curl http://localhost:8000/health`
- **Service Status**: `docker-compose ps`
- **Resource Usage**: `docker stats`
- **Ollama Status**: `ollama list`

### Logs
- **Application Logs**: `docker-compose logs hebrew-rag`
- **System Logs**: `journalctl -u docker`
- **Ollama Logs**: `journalctl -u ollama` (if running as service)

### Storage
- **Upload Directory**: `ls -la storage/uploads/`
- **Vector Database**: `ls -la storage/qdrant/`
- **Model Cache**: `ls -la storage/fastembed_cache/`
- **Ollama Models**: `ls -la ~/.ollama/models/`

## 🔍 Troubleshooting

### Common Issues

#### 1. Ollama Model Not Found
```bash
# Check if model is loaded
ollama list

# If not found, reload the model
cd ollama-models
./load_model.sh

# Restart Ollama service
sudo systemctl restart ollama
```

#### 2. Service Won't Start
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check Docker status
systemctl status docker
```

#### 3. Port Already in Use
```bash
# Check what's using port 8000
netstat -tlnp | grep :8000

# Change port in docker-compose.yml
# ports:
#   - "8001:8000"  # Use port 8001 instead
```

#### 4. Permission Issues
```bash
# Fix storage permissions
chmod -R 755 storage/
chown -R $USER:$USER storage/

# Fix Ollama permissions
sudo chown -R $USER:$USER ~/.ollama
```

#### 5. Memory Issues
```bash
# Check available memory
free -h

# Increase Docker memory limit
# Edit /etc/docker/daemon.json
# {
#   "default-shm-size": "2G"
# }
```

### Debug Mode
Enable debug logging by setting environment variables:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
docker-compose up -d
```

## 🔐 Security Considerations

### Network Security
- The application runs on `0.0.0.0:8000` by default
- Consider using a reverse proxy (nginx) for production
- Implement firewall rules to restrict access

### File Permissions
- Storage directories should have appropriate permissions
- Consider running as non-root user in production
- Ollama model files should be protected

### Environment Variables
- Use `.env` file for sensitive configuration
- Don't commit `.env` files to version control
- Use secrets management for production

## 📈 Performance Optimization

### Resource Allocation
- **CPU**: Allocate 4+ cores for optimal performance
- **RAM**: 32GB+ recommended for large document processing
- **Storage**: Use SSD for better I/O performance

### Model Optimization
- Models are pre-cached and optimized for inference
- Consider model quantization for memory-constrained environments
- Use GPU acceleration if available (requires additional setup)

### Database Optimization
- Qdrant vector database is optimized for Hebrew text
- Consider increasing memory limits for large document collections
- Monitor disk usage for vector storage

## 🔄 Updates and Maintenance

### Updating the System
1. Stop current services: `docker-compose down`
2. Backup data: `tar -czf backup-$(date +%Y%m%d).tar.gz storage/`
3. Load new image: `docker load < new-image.tar.gz`
4. Update docker-compose.yml if needed
5. Start services: `docker-compose up -d`

### Updating Ollama Model
1. Extract new model package: `tar -xzf new-ollama-model.tar.gz`
2. Load new model: `cd ollama-models && ./load_model.sh`
3. Verify: `ollama list`
4. Restart services if needed: `docker-compose restart`

### Backup and Recovery
```bash
# Create backup
tar -czf backup-$(date +%Y%m%d).tar.gz storage/

# Backup Ollama models
tar -czf ollama-backup-$(date +%Y%m%d).tar.gz ~/.ollama/models/

# Restore backup
tar -xzf backup-YYYYMMDD.tar.gz
tar -xzf ollama-backup-YYYYMMDD.tar.gz
```

### Log Rotation
```bash
# Configure log rotation in /etc/logrotate.d/docker
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

## 📞 Support

### Documentation
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Logs and Debugging
- **Application Logs**: `docker-compose logs hebrew-rag`
- **System Logs**: `journalctl -u docker`
- **Docker Logs**: `docker logs <container-id>`
- **Ollama Logs**: `journalctl -u ollama`

### Common Commands Reference
```bash
# Service management
docker-compose up -d          # Start services
docker-compose down           # Stop services
docker-compose restart        # Restart services
docker-compose ps             # Check status

# Logs and debugging
docker-compose logs           # View logs
docker-compose logs -f        # Follow logs
docker stats                  # Resource usage

# Data management
docker-compose exec hebrew-rag ls /app/storage/  # List storage
docker-compose exec hebrew-rag du -sh /app/storage/  # Check size

# Ollama management
ollama list                   # List models
ollama run gpt-oss:20b "test" # Test model
ollama rm gpt-oss:20b         # Remove model
```

## ✅ Verification Checklist

After deployment, verify all components are working:

- [ ] Docker containers are running
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] Web interface is accessible: http://localhost:8000
- [ ] API documentation loads: http://localhost:8000/docs
- [ ] Storage directories are created and writable
- [ ] Models are loaded and accessible
- [ ] Vector database is initialized
- [ ] File upload functionality works
- [ ] Document processing works
- [ ] Search functionality works
- [ ] Ollama model is loaded: `ollama list | grep gpt-oss`
- [ ] LLM responses work in the application

See `AIRGAPPED_CHECKLIST.md` for detailed verification steps.

---

**Note**: This system is designed to work completely offline. All ML models, dependencies, and runtime components are included in the packages. No internet connection is required for operation. 