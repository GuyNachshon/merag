import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List
import aiofiles
import os

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from models import (
    QueryRequest, QueryResponse, DocumentUploadResponse, 
    StatsResponse, ClearResponse, HealthResponse,
    IndexerStatusResponse, IndexerControlResponse
)
from config import settings
from services.rag_agent import rag_service
from services.periodic_indexer import periodic_indexer

from services.ocr_service import ocr_service
from services.transcription_service import transcription_service

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["Hebrew RAG"])

# Health endpoint
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={
            "rag_agent": "initialized" if rag_service.rag_agent.initialized else "not_initialized",
            "vector_store": "active",
            "llm": "active",
            "ocr": "active",
            "transcription": "active" if transcription_service.initialized else "not_initialized",
            "periodic_indexer": "active" if periodic_indexer.running else "inactive"
        },
        timestamp=datetime.utcnow().isoformat()
    )

# Query endpoint
@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the document collection"""
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Question cannot be empty"
            )
        
        result = await rag_service.query_documents(
            question=request.question,
            stream=request.stream
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return QueryResponse(
            success=True,
            response=result.get("response"),
            metadata=result.get("metadata")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Streaming query endpoint
@router.post("/query/stream")
async def query_documents_stream(request: QueryRequest):
    """Query the document collection with streaming response"""
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Question cannot be empty"
            )
        
        result = await rag_service.query_documents(
            question=request.question,
            stream=True
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        async def generate_response():
            try:
                async for chunk in result["response_generator"]:
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming query error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Document upload endpoint
@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    try:
        if not files:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No files provided"
            )
        
        # Validate file types
        allowed_extensions = set(settings.supported_extensions)
        uploaded_files = []
        
        for file in files:
            # Check file extension
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(allowed_extensions)}"
                )
            
            # Save uploaded file
            file_path = Path(settings.upload_dir) / file.filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                
                # Check file size
                file_size_mb = len(content) / (1024 * 1024)
                if file_size_mb > settings.max_file_size_mb:
                    raise HTTPException(
                        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"File {file.filename} is too large: {file_size_mb:.1f}MB (max: {settings.max_file_size_mb}MB)"
                    )
                
                await f.write(content)
            
            uploaded_files.append(str(file_path))
            logger.info(f"Saved uploaded file: {file_path}")
        
        # Process documents
        result = await rag_service.add_documents_from_files(uploaded_files)
        
        # Clean up uploaded files
        for file_path in uploaded_files:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {e}")
        
        return DocumentUploadResponse(
            success=result["success"],
            files_processed=result.get("files_processed", 0),
            files_failed=result.get("files_failed", 0),
            total_chunks=result.get("total_chunks", 0),
            documents_added=result.get("documents_added", 0),
            total_documents=result.get("total_documents", 0),
            error=result.get("error"),
            processing_details=result.get("processing_details")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Statistics endpoint
@router.get("/documents/stats", response_model=StatsResponse)
async def get_document_stats():
    """Get knowledge base statistics"""
    try:
        result = await rag_service.get_stats()
        
        return StatsResponse(
            success=result["success"],
            stats=result.get("stats", {}),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Clear documents endpoint
@router.delete("/documents/clear", response_model=ClearResponse)
async def clear_documents():
    """Clear all documents from the knowledge base"""
    try:
        result = await rag_service.clear_documents()
        
        return ClearResponse(
            success=result["success"],
            message=result.get("message"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Clear documents error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Periodic Indexer Management Endpoints
@router.get("/indexer/status", response_model=IndexerStatusResponse)
async def get_indexer_status():
    """Get periodic indexer status"""
    try:
        status = await periodic_indexer.get_status()
        return IndexerStatusResponse(
            success=True,
            status=status
        )
    except Exception as e:
        logger.error(f"Error getting indexer status: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/indexer/scan", response_model=IndexerControlResponse)
async def force_indexer_scan():
    """Force an immediate scan of the watch directory"""
    try:
        await periodic_indexer.force_scan()
        return IndexerControlResponse(
            success=True,
            message="Directory scan completed"
        )
    except Exception as e:
        logger.error(f"Error forcing indexer scan: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/indexer/start", response_model=IndexerControlResponse)
async def start_indexer():
    """Start the periodic indexer"""
    try:
        await periodic_indexer.start()
        return IndexerControlResponse(
            success=True,
            message="Periodic indexer started"
        )
    except Exception as e:
        logger.error(f"Error starting indexer: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/indexer/stop", response_model=IndexerControlResponse)
async def stop_indexer():
    """Stop the periodic indexer"""
    try:
        await periodic_indexer.stop()
        return IndexerControlResponse(
            success=True,
            message="Periodic indexer stopped"
        )
    except Exception as e:
        logger.error(f"Error stopping indexer: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# OCR Processing Endpoints
@router.post("/ocr/process-image")
async def process_image_ocr(
    file: UploadFile = File(...),
    task_type: str = "full"
):
    """Process image with OCR"""
    try:
        if not file:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No file provided"
            )
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must be an image"
            )
        
        # Save uploaded file temporarily
        file_path = Path(settings.upload_dir) / f"ocr_temp_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        try:
            # Process with OCR
            result = await ocr_service.extract_text_from_image(
                file_path, 
                task_type=task_type
            )
            
            return {
                "success": result["success"],
                "text": result.get("text", ""),
                "method": result.get("method", ""),
                "task_type": result.get("task_type", task_type),
                "parsed": result.get("parsed"),
                "error": result.get("error")
            }
            
        finally:
            # Clean up temporary file
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/ocr/process-pdf")
async def process_pdf_ocr(
    file: UploadFile = File(...),
    task_type: str = "full"
):
    """Process PDF with OCR"""
    try:
        if not file:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No file provided"
            )
        
        # Validate file type
        if file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must be a PDF"
            )
        
        # Save uploaded file temporarily
        file_path = Path(settings.upload_dir) / f"ocr_temp_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        try:
            # Process with OCR
            result = await ocr_service.extract_text_from_pdf(
                file_path, 
                task_type=task_type
            )
            
            return {
                "success": result["success"],
                "text": result.get("text", ""),
                "method": result.get("method", ""),
                "task_type": result.get("task_type", task_type),
                "total_pages": result.get("total_pages", 0),
                "pages": result.get("pages", []),
                "error": result.get("error")
            }
            
        finally:
            # Clean up temporary file
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF OCR processing error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/ocr/status")
async def get_ocr_status():
    """Get OCR service status"""
    try:
        return {
            "dots_ocr_available": ocr_service.dots_ocr.is_available(),
            "tesseract_available": ocr_service.tesseract_ocr.is_available(),
            "initialized": ocr_service.initialized,
            "model_name": ocr_service.dots_ocr.model_name if ocr_service.dots_ocr.is_available() else None
        }
    except Exception as e:
        logger.error(f"Error getting OCR status: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/system/validation")
async def validate_system_configuration():
    """Validate system configuration and environment"""
    try:
        from config import settings
        validation_result = await settings.validate_configuration()
        return validation_result
    except Exception as e:
        logger.error(f"Error validating system configuration: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/system/memory")
async def get_memory_usage():
    """Get current memory usage information"""
    try:
        memory_info = {}
        
        # Get OCR service memory usage
        if ocr_service.dots_ocr.is_available():
            memory_info["ocr_service"] = ocr_service.dots_ocr.get_memory_usage()
        
        # Get system memory usage
        try:
            import psutil
            memory_info["system"] = {
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available": f"{psutil.virtual_memory().available / 1024**3:.2f} GB",
                "memory_total": f"{psutil.virtual_memory().total / 1024**3:.2f} GB"
            }
        except ImportError:
            memory_info["system"] = {"error": "psutil not available"}
        
        return memory_info
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/system/cleanup")
async def cleanup_memory():
    """Clean up memory and GPU cache"""
    try:
        # Clean up OCR service memory
        if ocr_service.dots_ocr.is_available():
            await ocr_service.dots_ocr.cleanup_memory()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        return {
            "success": True,
            "message": "Memory cleanup completed successfully"
        }
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Transcription endpoints
@router.post("/transcribe/audio")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "he",
    task: str = "transcribe",
    output_format: str = "text"
):
    """Transcribe audio file to text"""
    try:
        if not file:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No file provided"
            )
        
        # Validate file type
        allowed_audio_types = [
            'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg', 
            'audio/flac', 'audio/aac', 'audio/webm', 'audio/m4a'
        ]
        
        if file.content_type not in allowed_audio_types:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported audio format: {file.content_type}. Supported formats: {', '.join(allowed_audio_types)}"
            )
        
        # Save uploaded file temporarily
        file_path = Path(settings.upload_dir) / f"transcribe_temp_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            
            # Check file size (max 100MB for audio)
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > 100:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Audio file is too large: {file_size_mb:.1f}MB (max: 100MB)"
                )
            
            await f.write(content)
        
        try:
            # Transcribe audio
            result = await transcription_service.transcribe_audio_file(
                str(file_path),
                output_format=output_format
            )
            
            if not result["success"]:
                raise HTTPException(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Transcription failed")
                )
            
            return {
                "success": True,
                "text": result["text"],
                "language": result["language"],
                "task": result["task"],
                "model": result["model"],
                "metadata": result.get("metadata", {})
            }
            
        finally:
            # Clean up temporary file
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/transcribe/status")
async def get_transcription_status():
    """Get transcription service status"""
    return {
        "service": "hebrew_transcription",
        "model": transcription_service.model_name,
        "initialized": transcription_service.initialized,
        "device": transcription_service.device,
        "status": "active" if transcription_service.initialized else "not_initialized"
    }