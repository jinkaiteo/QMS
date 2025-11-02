"""
Document File Management API Endpoints
Handles file upload, download, versioning, and dependencies
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from io import BytesIO

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.file_management_service import FileManagementService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Pydantic models for request/response

class FileUploadResponse(BaseModel):
    version_id: int
    version_number: str
    file_path: str
    file_size: int
    checksum: str
    mime_type: str
    message: str

class DocumentVersionResponse(BaseModel):
    id: int
    version_number: str
    major_version: int
    minor_version: int
    file_name: str
    file_size: int
    mime_type: str
    is_current: bool
    is_official: bool
    upload_reason: str
    created_at: datetime
    uploaded_by: str

class DependencyCreateRequest(BaseModel):
    dependent_document_id: int
    dependency_type: str = Field(..., pattern="^(references|supersedes|implements|requires)$")
    notes: str = ""

class DependencyResponse(BaseModel):
    dependency_id: int
    dependency_type: str
    notes: str
    document_id: int
    document_number: str
    title: str
    status: str
    created_by: str

class DocumentDependenciesResponse(BaseModel):
    parents: List[DependencyResponse]
    dependents: List[DependencyResponse]

# File upload endpoints

@router.post("/{document_id}/upload", response_model=FileUploadResponse)
async def upload_document_file(
    document_id: int,
    file: UploadFile = File(..., description="Document file to upload"),
    version_number: Optional[str] = Form(None, description="Version number (auto-generated if not provided)"),
    upload_reason: str = Form("File upload", description="Reason for uploading this version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new file version for a document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")
        
        # Validate file type (basic check)
        allowed_types = {
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        if file.content_type not in allowed_types:
            logger.warning(f"File type {file.content_type} uploaded for document {document_id}")
            # Allow but warn - don't reject
        
        service = FileManagementService(db)
        
        # Create BytesIO object from file content
        file_io = BytesIO(file_content)
        
        result = service.upload_document_file(
            document_id=document_id,
            file_content=file_io,
            filename=file.filename,
            user_id=current_user.id,
            version_number=version_number,
            upload_reason=upload_reason
        )
        
        return FileUploadResponse(
            version_id=result['version_id'],
            version_number=result['version_number'],
            file_path=result['file_path'],
            file_size=result['file_size'],
            checksum=result['checksum'],
            mime_type=result['mime_type'],
            message=f"File uploaded successfully as version {result['version_number']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

# File download endpoints

@router.get("/{document_id}/download")
async def download_document_file(
    document_id: int,
    version_number: Optional[str] = Query(None, description="Specific version to download"),
    download_type: str = Query("original", description="Download type: original, annotated, or official_pdf"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a document file"""
    try:
        # Validate download type
        valid_types = ['original', 'annotated', 'official_pdf']
        if download_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid download type. Must be one of: {valid_types}")
        
        service = FileManagementService(db)
        
        result = service.download_document_file(
            document_id=document_id,
            version_number=version_number,
            download_type=download_type
        )
        
        if not result['content']:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Create streaming response
        file_stream = BytesIO(result['content'])
        
        # Set appropriate headers
        headers = {
            'Content-Disposition': f'attachment; filename="{result["filename"]}"',
            'Content-Length': str(result['file_size'])
        }
        
        return StreamingResponse(
            BytesIO(result['content']),
            media_type=result['mime_type'],
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

# Version management endpoints

@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions for a document"""
    try:
        service = FileManagementService(db)
        versions = service.get_document_versions(document_id)
        
        return [DocumentVersionResponse(**version) for version in versions]
        
    except Exception as e:
        logger.error(f"Error getting versions for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document versions: {str(e)}")

@router.delete("/versions/{version_id}")
async def delete_document_version(
    version_id: int,
    reason: str = Query("Version deletion", description="Reason for deletion"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document version (soft delete)"""
    try:
        service = FileManagementService(db)
        
        success = service.delete_document_version(
            version_id=version_id,
            user_id=current_user.id,
            reason=reason
        )
        
        if success:
            return {"message": "Version deleted successfully", "version_id": version_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete version")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting version {version_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete version: {str(e)}")

# Document dependencies endpoints

@router.post("/{document_id}/dependencies")
async def create_document_dependency(
    document_id: int,
    request: DependencyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a dependency relationship between documents"""
    try:
        service = FileManagementService(db)
        
        result = service.create_document_dependency(
            parent_document_id=document_id,
            dependent_document_id=request.dependent_document_id,
            dependency_type=request.dependency_type,
            user_id=current_user.id,
            notes=request.notes
        )
        
        return {
            "message": f"Dependency created: {request.dependency_type}",
            "dependency_id": result['dependency_id'],
            "parent_document_id": result['parent_document_id'],
            "dependent_document_id": result['dependent_document_id']
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating dependency for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create dependency: {str(e)}")

@router.get("/{document_id}/dependencies", response_model=DocumentDependenciesResponse)
async def get_document_dependencies(
    document_id: int,
    direction: str = Query("both", description="Direction: parent, dependent, or both"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dependency relationships for a document"""
    try:
        # Validate direction
        valid_directions = ['parent', 'dependent', 'both']
        if direction not in valid_directions:
            raise HTTPException(status_code=400, detail=f"Invalid direction. Must be one of: {valid_directions}")
        
        service = FileManagementService(db)
        dependencies = service.get_document_dependencies(document_id, direction)
        
        return DocumentDependenciesResponse(
            parents=[DependencyResponse(**dep) for dep in dependencies['parents']],
            dependents=[DependencyResponse(**dep) for dep in dependencies['dependents']]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dependencies for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dependencies: {str(e)}")

@router.delete("/dependencies/{dependency_id}")
async def delete_document_dependency(
    dependency_id: int,
    reason: str = Query("Dependency removal", description="Reason for removing dependency"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a document dependency relationship"""
    try:
        from sqlalchemy import text
        
        # Soft delete the dependency
        query = text("""
            UPDATE document_dependencies 
            SET is_deleted = TRUE, updated_at = NOW()
            WHERE id = :dependency_id
        """)
        
        result = db.execute(query, {'dependency_id': dependency_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Dependency not found")
        
        db.commit()
        
        return {
            "message": "Dependency removed successfully",
            "dependency_id": dependency_id,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dependency {dependency_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete dependency: {str(e)}")

# Utility endpoints

@router.get("/{document_id}/storage-info")
async def get_document_storage_info(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get storage information for a document"""
    try:
        service = FileManagementService(db)
        
        # Get current version info
        from sqlalchemy import text
        query = text("""
            SELECT 
                COUNT(*) as total_versions,
                SUM(file_size) as total_size,
                MAX(created_at) as last_upload,
                STRING_AGG(DISTINCT mime_type, ', ') as file_types
            FROM document_versions 
            WHERE document_id = :document_id AND is_deleted = FALSE
        """)
        
        result = db.execute(query, {'document_id': document_id})
        row = result.fetchone()
        
        storage_info = {
            'document_id': document_id,
            'total_versions': row.total_versions or 0,
            'total_size_bytes': row.total_size or 0,
            'total_size_mb': round((row.total_size or 0) / 1024 / 1024, 2),
            'last_upload': row.last_upload,
            'file_types': row.file_types or 'None',
            'storage_backend': 'MinIO' if service.storage_available else 'Local'
        }
        
        return storage_info
        
    except Exception as e:
        logger.error(f"Error getting storage info for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get storage info: {str(e)}")

@router.post("/{document_id}/generate-official-pdf")
async def generate_official_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate an official PDF for an approved document"""
    try:
        service = FileManagementService(db)
        
        # Check if document is approved
        from sqlalchemy import text
        query = text("SELECT status FROM documents WHERE id = :document_id")
        result = db.execute(query, {'document_id': document_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if row.status != 'approved':
            raise HTTPException(status_code=400, detail="Official PDF can only be generated for approved documents")
        
        # Generate and download official PDF
        download_result = service.download_document_file(
            document_id=document_id,
            download_type='official_pdf'
        )
        
        # Create streaming response
        headers = {
            'Content-Disposition': f'attachment; filename="{download_result["filename"]}"',
            'Content-Length': str(download_result['file_size'])
        }
        
        return StreamingResponse(
            BytesIO(download_result['content']),
            media_type='application/pdf',
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating official PDF for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate official PDF: {str(e)}")

# Health check endpoint
@router.get("/health")
async def file_management_health_check():
    """Health check for file management service"""
    try:
        # Test storage availability
        service = FileManagementService(None)  # Don't need DB for health check
        
        return {
            "status": "healthy",
            "service": "document_files",
            "timestamp": datetime.now(),
            "storage_backend": "MinIO" if service.storage_available else "Local",
            "endpoints_available": [
                "upload", "download", "versions", 
                "dependencies", "storage-info", "generate-official-pdf"
            ]
        }
        
    except Exception as e:
        logger.error(f"File management health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "document_files",
            "timestamp": datetime.now(),
            "error": str(e)
        }