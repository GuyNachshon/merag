from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Vector Store Configuration
    qdrant_path: str = "./storage/qdrant"
    qdrant_collection_name: str = "hebrew_documents"

    # OCR Configuration
    dots_ocr_model: str = "rednote-hilab/dots.ocr"
    dots_ocr_fallback_model: str = "microsoft/DialoGPT-medium"  # Fallback if dots.ocr fails
    tesseract_lang: str = "heb+eng"

    # LLM Configuration
    llm_model: str = "gpt-oss:20b"  # Default to GPT-OSS for Hebrew
    ollama_host: str = "http://localhost:11434"

    # Embedding Configuration (FastEmbed)
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_dimension: int = 1024  # multilingual-e5-large dimension

    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 100
    supported_extensions: List[str] = [".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".mp3", ".wav", ".m4a", ".flac"]

    # Storage Configuration
    upload_dir: str = "./storage/uploads"
    vector_db_dir: str = "./storage/vector_db"
    
    # Periodic Indexing Configuration
    watch_directory: str = "./storage/watch"  # Directory to monitor for new files
    scan_interval_seconds: int = 3600  # How often to scan for new files
    enable_periodic_indexing: bool = True  # Enable/disable periodic indexing
    processed_files_db: str = "./storage/processed_files.json"  # Track processed files

    # Hebrew Language Settings
    hebrew_text_direction: str = "rtl"
    hebrew_tokenizer: bool = True

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and environment"""
        validation_results = {
            "overall_status": "valid",
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "info": [],
            "environment_info": {}
        }
        
        try:
            # Check storage directories
            await self._validate_storage_directories(validation_results)
            
            # Check model availability
            await self._validate_models(validation_results)
            
            # Check environment
            await self._validate_environment(validation_results)
            
            # Check dependencies
            await self._validate_dependencies(validation_results)
            
            # Determine overall status (ignore optional dependency warnings)
            critical_warnings = [w for w in validation_results["warnings"] if "optional dependency" not in w]
            
            if validation_results["errors"]:
                validation_results["overall_status"] = "error"
            elif critical_warnings:
                validation_results["overall_status"] = "warning"
            else:
                validation_results["overall_status"] = "valid"
            
        except Exception as e:
            validation_results["errors"].append(f"Configuration validation failed: {str(e)}")
            validation_results["overall_status"] = "error"
        
        return validation_results
    
    async def _validate_storage_directories(self, results: Dict[str, Any]):
        """Validate storage directories exist and are writable"""
        directories = [
            self.upload_dir,
            self.qdrant_path,
            self.vector_db_dir,
            self.watch_directory
        ]
        
        for directory in directories:
            try:
                path = Path(directory)
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    results["warnings"].append(f"Created missing directory: {directory}")
                
                # Test write access
                test_file = path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
                
            except Exception as e:
                results["errors"].append(f"Directory {directory} is not writable: {str(e)}")
    
    async def _validate_models(self, results: Dict[str, Any]):
        """Validate model configurations"""
        try:
            # Check dots.ocr model
            if self.dots_ocr_model:
                results["environment_info"]["dots_ocr_model"] = self.dots_ocr_model
            
            # Check LLM model
            if self.llm_model:
                results["environment_info"]["llm_model"] = self.llm_model
            
            # Check embedding model
            if self.embedding_model:
                results["environment_info"]["embedding_model"] = self.embedding_model
                
        except Exception as e:
            results["warnings"].append(f"Model validation warning: {str(e)}")
    
    async def _validate_environment(self, results: Dict[str, Any]):
        """Validate environment and hardware"""
        try:
            # Check Python version
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            results["environment_info"]["python_version"] = python_version
            
            if sys.version_info < (3, 8):
                results["errors"].append("Python 3.8+ is required")
            
            # Check CUDA availability
            try:
                import torch
                cuda_available = torch.cuda.is_available()
                results["environment_info"]["cuda_available"] = cuda_available
                
                if cuda_available:
                    gpu_count = torch.cuda.device_count()
                    gpu_name = torch.cuda.get_device_name(0)
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    
                    results["environment_info"]["gpu_count"] = gpu_count
                    results["environment_info"]["gpu_name"] = gpu_name
                    results["environment_info"]["gpu_memory_gb"] = f"{gpu_memory:.1f}"
                    
                    if gpu_memory < 8:
                        results["warnings"].append(f"Low GPU memory ({gpu_memory:.1f}GB). Consider using CPU or smaller models.")
                    else:
                        results["recommendations"].append("GPU detected - optimal for dots.ocr processing")
                else:
                    results["warnings"].append("CUDA not available - dots.ocr will use CPU (slower)")
                    
            except ImportError:
                results["warnings"].append("PyTorch not available - CUDA check skipped")
            
            # Check system memory
            try:
                import psutil
                memory = psutil.virtual_memory()
                memory_gb = memory.total / 1024**3
                results["environment_info"]["system_memory_gb"] = f"{memory_gb:.1f}"
                
                if memory_gb < 8:
                    results["warnings"].append(f"Low system memory ({memory_gb:.1f}GB). Consider increasing RAM.")
                    
            except ImportError:
                results["warnings"].append("psutil not available - memory check skipped")
                
        except Exception as e:
            results["warnings"].append(f"Environment validation warning: {str(e)}")
    
    async def _validate_dependencies(self, results: Dict[str, Any]):
        """Validate required dependencies"""
        import platform
        is_mac = platform.system() == "Darwin"
        
        dependencies = {
            "torch": "PyTorch for dots.ocr",
            "transformers": "Transformers for dots.ocr",
            "qwen_vl_utils": "Qwen VL utils for dots.ocr",
            "fastembed": "FastEmbed for embeddings",
            "qdrant_client": "Qdrant client for vector store",
            "fitz": "PyMuPDF for PDF processing",
            "pytesseract": "Tesseract for OCR fallback"
        }
        
        # Optional dependencies (warnings only)
        optional_dependencies = {
            "flash_attn": "Flash attention for faster inference (optional)",
            "librosa": "Audio processing",
            "psutil": "System monitoring"
        }
        
        for package, description in dependencies.items():
            try:
                __import__(package)
                results["environment_info"][f"{package}_available"] = True
            except ImportError:
                results["warnings"].append(f"Missing dependency: {package} ({description})")
                results["environment_info"][f"{package}_available"] = False
        
        # Check optional dependencies
        for package, description in optional_dependencies.items():
            try:
                __import__(package)
                results["environment_info"][f"{package}_available"] = True
            except ImportError:
                if package == "flash_attn" and is_mac:
                    results["info"].append("flash_attn not available on macOS (CUDA-only)")
                    results["environment_info"][f"{package}_available"] = False
                else:
                    results["warnings"].append(f"Missing optional dependency: {package} ({description})")
                    results["environment_info"][f"{package}_available"] = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.qdrant_path, exist_ok=True)
os.makedirs(settings.vector_db_dir, exist_ok=True)
os.makedirs(settings.watch_directory, exist_ok=True)
