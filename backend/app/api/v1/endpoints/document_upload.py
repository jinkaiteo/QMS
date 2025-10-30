"""
Document Upload API Endpoints
File upload and storage management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.edms import Document, DocumentType, DocumentCategory, DocumentVersion
from app.services.document_storage_service import document_storage_service
# Using dict responses for now - can add proper schemas later

router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    document_type_id: int = Form(...),
    category_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new document with file storage"""
    
    # Validate file type
    if not document_storage_service.validate_file_type(file.filename):
        raise HTTPException(
            status_code=400, 
            detail="File type not allowed. Supported types: PDF, Word, Excel, PowerPoint, images"
        )
    
    # Validate file size (50MB limit)
    if file.size and not document_storage_service.validate_file_size(file.size):
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum size: 50MB"
        )
    
    # Verify document type exists
    document_type = db.query(DocumentType).filter(DocumentType.id == document_type_id).first()
    if not document_type:
        raise HTTPException(status_code=404, detail="Document type not found")
    
    # Verify category exists (if provided)
    if category_id:
        category = db.query(DocumentCategory).filter(DocumentCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Document category not found")
    
    try:
        # Upload file to storage
        file_path, file_info = await document_storage_service.upload_file(
            file=file,
            document_type=document_type.code.lower(),
            metadata={
                "title": title,
                "uploaded_by": current_user.username,
                "document_type": document_type.name
            }
        )
        
        # Create document record in database
        document = Document(
            title=title,
            description=description,
            document_type_id=document_type_id,
            category_id=category_id,
            created_by_id=current_user.id,
            status="draft",
            file_path=file_path,
            file_name=file.filename,
            file_size=file_info["size"],
            mime_type=file_info["content_type"],
            file_hash=file_info["hash"]
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Create initial version record
        version = DocumentVersion(
            document_id=document.id,
            version_number="1.0",
            file_path=file_path,
            file_name=file.filename,
            file_size=file_info["size"],
            mime_type=file_info["content_type"],
            file_hash=file_info["hash"],
            created_by_id=current_user.id,
            change_summary="Initial upload"
        )
        
        db.add(version)
        db.commit()
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "file_path": file_path,
            "file_info": file_info,
            "version": "1.0"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{document_id}")
async def download_document(
    document_id: int,
    version: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a document file"""
    
    # Get document record
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Determine which version to download
    if version:
        doc_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version
        ).first()
        if not doc_version:
            raise HTTPException(status_code=404, detail="Document version not found")
        file_path = doc_version.file_path
        filename = doc_version.file_name
    else:
        # Download latest version
        file_path = document.file_path
        filename = document.file_name
    
    try:
        # Get file from storage
        file_data, metadata = document_storage_service.download_file(file_path)
        
        from fastapi.responses import Response
        return Response(
            content=file_data,
            media_type=metadata["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(file_data))
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/preview/{document_id}")
async def preview_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a presigned URL for document preview"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Generate presigned URL for temporary access
        presigned_url = document_storage_service.generate_presigned_url(
            document.file_path
        )
        
        return {
            "document_id": document_id,
            "title": document.title,
            "filename": document.file_name,
            "content_type": document.mime_type,
            "preview_url": presigned_url,
            "expires_in": "1 hour"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/list")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    document_type_id: Optional[int] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents with filtering options"""
    
    query = db.query(Document)
    
    # Apply filters
    if document_type_id:
        query = query.filter(Document.document_type_id == document_type_id)
    
    if category_id:
        query = query.filter(Document.category_id == category_id)
    
    if status:
        query = query.filter(Document.status == status)
    
    # Get documents with pagination
    documents = query.offset(skip).limit(limit).all()
    total_count = query.count()
    
    # Format response
    document_list = []
    for doc in documents:
        document_list.append({
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "status": doc.status,
            "file_name": doc.file_name,
            "file_size": doc.file_size,
            "mime_type": doc.mime_type,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
            "created_by": doc.created_by_id,
            "document_type_id": doc.document_type_id,
            "category_id": doc.category_id
        })
    
    return {
        "documents": document_list,
        "total": total_count,
        "page": skip // limit + 1,
        "per_page": limit,
        "total_pages": (total_count + limit - 1) // limit
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its file"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user has permission to delete (implement as needed)
    if document.created_by_id != current_user.id:
        # Add role-based permission check here
        pass
    
    try:
        # Delete file from storage
        document_storage_service.delete_file(document.file_path)
        
        # Delete all versions
        db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).delete()
        
        # Delete document record
        db.delete(document)
        db.commit()
        
        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
):
    """Get storage usage statistics"""
    
    try:
        # Get file list for statistics
        files = document_storage_service.list_files(limit=1000)
        
        total_files = len(files)
        total_size = sum(f["size"] for f in files)
        
        # Convert size to human readable
        def human_readable_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_human": human_readable_size(total_size),
            "bucket_name": document_storage_service.bucket_name,
            "storage_service": "MinIO"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")