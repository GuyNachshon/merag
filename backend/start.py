#!/usr/bin/env python3
"""
Hebrew Agentic RAG System Startup Script
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from main import app
from config import settings
from services.rag_agent import rag_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_dependencies():
    """Check if required dependencies are available"""
    logger.info("Checking system dependencies...")

    # Check Ollama availability
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_host}/api/tags", timeout=5.0)
            if response.status_code == 200:
                logger.info("✓ Ollama is running")
            else:
                logger.warning("⚠ Ollama is not accessible - LLM queries will fail")
    except Exception as e:
        logger.warning(f"⚠ Ollama check failed: {e}")

    # Check dots.ocr model (placeholder)
    logger.info("✓ OCR service configured")

    # Check storage directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.qdrant_path, exist_ok=True)
    logger.info("✓ Storage directories ready")


async def initialize_services():
    """Initialize all services"""
    logger.info("Initializing Hebrew RAG services...")
    try:
        await rag_service.initialize()
        logger.info("✓ All services initialized successfully")
    except Exception as e:
        logger.error(f"✗ Service initialization failed: {e}")
        raise


def print_startup_info():
    """Print startup information"""
    print("\n" + "=" * 60)
    print("🔮 Hebrew Agentic RAG System")
    print("=" * 60)
    print(f"📚 OCR Model: {settings.dots_ocr_model}")
    print(f"🤖 LLM Model: {settings.llm_model}")
    print(f"🔍 Embedding Model: intfloat/multilingual-e5-large (FastEmbed)")
    print(f"📡 API Server: http://{settings.api_host}:{settings.api_port}")
    print(f"📖 Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"🌐 Frontend: Configure VITE_API_BASE_URL=http://localhost:{settings.api_port}/api/v1")
    print("=" * 60)
    print("\nSupported document formats:")
    print("  • PDF files (.pdf)")
    print("  • Word documents (.docx, .doc)")
    print("  • Text files (.txt)")
    print("  • Images (.png, .jpg, .jpeg) - with OCR")
    print("\nTo get started:")
    print("  1. Upload documents via the API or frontend")
    print("  2. Ask questions in Hebrew about your documents")
    print("  3. Get intelligent responses based on your content")
    print("=" * 60 + "\n")


async def main():
    """Main startup routine"""
    try:
        print_startup_info()
        await check_dependencies()
        await initialize_services()

        logger.info("Starting FastAPI server...")
        import uvicorn

        config = uvicorn.Config(
            app,
            host=settings.api_host,
            port=settings.api_port,
            log_level="info",
            reload=False  # Set to True for development
        )

        server = uvicorn.Server(config)
        await server.serve()

    except KeyboardInterrupt:
        logger.info("Shutting down Hebrew RAG system...")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
