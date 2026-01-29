"""
Document Management API
Endpoints for uploading and managing documents in RAG system
"""

import os
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import tempfile
from pathlib import Path

from ..ai.rag_service import RAGService

router = APIRouter()

# Initialize RAG service
rag_service = None


def get_rag_service():
    """Get or create RAG service instance"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService(persist_directory="./chroma_db")
    return rag_service


class DocumentUploadResponse(BaseModel):
    filename: str
    chunk_count: int
    file_size: int
    status: str


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    chunk_index: int
    total_chunks: int
    timestamp: str


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


class SearchResult(BaseModel):
    text: str
    metadata: dict
    distance: float = None


class RAGStats(BaseModel):
    total_chunks: int
    unique_documents: int
    file_types: dict
    collection_name: str


@router.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to RAG system

    Supports: .txt, .pdf, .docx, .xls, .xlsx

    Automatically detects service catalogs (HTML tables) and loads each service separately
    """
    try:
        rag = get_rag_service()

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        supported_types = ['.txt', '.pdf', '.docx', '.doc', '.xls', '.xlsx']

        if file_ext not in supported_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {', '.join(supported_types)}"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Check if this is a service catalog (HTML table in .xls file)
            is_service_catalog = False
            if file_ext in ['.xls', '.xlsx']:
                with open(tmp_path, 'rb') as f:
                    header = f.read(200)
                    if header.startswith(b'<html') or b'<table' in header.lower():
                        # Check if it looks like a service catalog (has specific headers)
                        if b'Tj\xc3\xa4nst' in header or b'Service' in header or b'Ingress' in header:
                            is_service_catalog = True
                            print(f"🎯 Detected service catalog in {file.filename}")

            # Use specialized loader for service catalogs
            if is_service_catalog:
                from ..ai.service_catalog_loader import ServiceCatalogLoader
                loader = ServiceCatalogLoader(rag)
                result = loader.load_html_service_catalog(tmp_path)
                return DocumentUploadResponse(
                    filename=file.filename,
                    chunk_count=result['services_loaded'],
                    file_size=len(content),
                    status="success"
                )
            else:
                # Regular document processing
                result = rag.add_document(tmp_path)
                return DocumentUploadResponse(**result)
        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except Exception as e:
        print(f"❌ Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/upload-text", response_model=DocumentUploadResponse)
async def upload_text(filename: str, text: str):
    """Upload raw text to RAG system"""
    try:
        rag = get_rag_service()
        result = rag.add_text(text, filename)
        return DocumentUploadResponse(**result)
    except Exception as e:
        print(f"❌ Error uploading text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    """Search for relevant documents"""
    try:
        rag = get_rag_service()
        results = rag.search(request.query, request.n_results)
        return [SearchResult(**r) for r in results]
    except Exception as e:
        print(f"❌ Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents", response_model=List[dict])
async def get_all_documents():
    """Get all documents in RAG system"""
    try:
        rag = get_rag_service()
        documents = rag.get_all_documents()
        return documents
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/files", response_model=List[dict])
async def get_unique_files():
    """Get list of unique files with metadata"""
    try:
        rag = get_rag_service()
        all_docs = rag.get_all_documents()

        # Group by filename
        files_dict = {}
        for doc in all_docs:
            metadata = doc.get('metadata', {})
            filename = metadata.get('filename', 'unknown')

            if filename not in files_dict:
                files_dict[filename] = {
                    'filename': filename,
                    'chunk_count': 0,
                    'file_type': metadata.get('file_type', 'unknown'),
                    'source': metadata.get('source', 'unknown'),
                    'service_type': metadata.get('service_type', None),
                    'first_seen': metadata.get('timestamp', None)
                }

            files_dict[filename]['chunk_count'] += 1

        return list(files_dict.values())
    except Exception as e:
        print(f"❌ Error getting files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document from RAG system"""
    try:
        rag = get_rag_service()
        result = rag.delete_document(filename)
        return result
    except Exception as e:
        print(f"❌ Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/stats", response_model=RAGStats)
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        rag = get_rag_service()
        stats = rag.get_stats()
        return RAGStats(**stats)
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/clear")
async def clear_collection():
    """Clear all documents from RAG system"""
    try:
        rag = get_rag_service()
        rag.clear_collection()
        return {"status": "success", "message": "Collection cleared"}
    except Exception as e:
        print(f"❌ Error clearing collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/upload-service-catalog")
async def upload_service_catalog(file: UploadFile = File(...)):
    """
    Upload service catalog with each service as separate document for better matching

    Optimized for HTML tables with service information
    """
    try:
        from ..ai.service_catalog_loader import ServiceCatalogLoader

        rag = get_rag_service()
        loader = ServiceCatalogLoader(rag)

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Load with specialized catalog loader
            result = loader.load_html_service_catalog(tmp_path)
            return {
                "filename": file.filename,
                "services_loaded": result['services_loaded'],
                "total_chunks": result['total_chunks'],
                "status": "success"
            }
        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except Exception as e:
        print(f"❌ Error uploading service catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))
