import logging
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from api.routes import router
from services.rag_agent import rag_service
from services.periodic_indexer import periodic_indexer
from services.transcription_service import transcription_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting Hebrew Agentic RAG API...")
    try:
        # Validate configuration first
        logger.info("Validating configuration and environment...")
        validation_result = await settings.validate_configuration()
        
        if validation_result["overall_status"] == "error":
            logger.error("Configuration validation failed:")
            for error in validation_result["errors"]:
                logger.error(f"  - {error}")
            raise RuntimeError("Configuration validation failed")
        
        if validation_result["overall_status"] == "warning":
            logger.warning("Configuration validation warnings:")
            for warning in validation_result["warnings"]:
                logger.warning(f"  - {warning}")
        
        if validation_result["recommendations"]:
            logger.info("Configuration recommendations:")
            for rec in validation_result["recommendations"]:
                logger.info(f"  - {rec}")
        
        logger.info("Configuration validation completed successfully")
        
        # Initialize services
        await rag_service.initialize()
        logger.info("RAG service initialized successfully")
        
        # Initialize transcription service
        await transcription_service.initialize()
        logger.info("Transcription service initialized successfully")
        
        # Initialize and start periodic indexer
        await periodic_indexer.initialize()
        await periodic_indexer.start()
        logger.info("Periodic indexer started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hebrew Agentic RAG API...")
    try:
        await periodic_indexer.stop()
        logger.info("Periodic indexer stopped")
        
        await transcription_service.close()
        logger.info("Transcription service stopped")
        
    except Exception as e:
        logger.error(f"Error stopping services: {e}")

# Create FastAPI app
app = FastAPI(
    title="Hebrew Agentic RAG API",
    description="Local agentic RAG system for Hebrew documents with OCR support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Hebrew Agentic RAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "features": [
            "Hebrew document processing",
            "Multi-format support (PDF, DOCX, images)",
            "OCR with dots.ocr + Tesseract fallback",
            "Qdrant vector storage",
            "Agentic RAG with multiple LLM options",
            "Streaming responses",
            "Vue.js frontend integration"
        ]
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )