from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to ask the RAG system")
    stream: bool = Field(False, description="Whether to stream the response")

class QueryResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentUploadResponse(BaseModel):
    success: bool
    files_processed: int
    files_failed: int
    total_chunks: int
    documents_added: int
    total_documents: int
    error: Optional[str] = None
    processing_details: Optional[Dict[str, Any]] = None

class StatsResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]
    error: Optional[str] = None

class ClearResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
    timestamp: str

class IndexerStatusResponse(BaseModel):
    """Response model for indexer status"""
    success: bool
    status: Dict[str, Any]

class IndexerControlResponse(BaseModel):
    """Response model for indexer control operations"""
    success: bool
    message: str

__all__ = [
    "QueryRequest",
    "QueryResponse", 
    "DocumentUploadResponse",
    "StatsResponse",
    "ClearResponse",
    "HealthResponse",
    "IndexerStatusResponse",
    "IndexerControlResponse"
]