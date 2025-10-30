# Documents API Endpoints - Phase 2 EDMS
# RESTful API for document management

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.edms import Document, DocumentType, DocumentCategory
from app.schemas.edms import (
    Document as DocumentSchema,
    DocumentList,
    DocumentCreate,
    DocumentUpdate,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentType as DocumentTypeSchema,
    DocumentTypeCreate,
    DocumentTypeUpdate,
    DocumentCategory as DocumentCategorySchema,
    DocumentCategoryCreate,
    DocumentCategoryUpdate,
    StartReviewRequest,
    CompleteReviewRequest,
    ApproveDocumentRequest,
    DocumentWorkflow as DocumentWorkflowSchema,
    FileUploadResponse,
    DownloadRequest
)
from app.services.document_service import DocumentService
from app.core.config import settings

router = APIRouter()


# Document Type endpoints
@router.get("/types", response_model=List[DocumentTypeSchema])
async def get_document_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all document types"""
    document_types = db.query(DocumentType).filter(
        DocumentType.is_active == True
    ).offset(skip).limit(limit).all()
    
    return document_types


@router.post("/types", response_model=DocumentTypeSchema)
async def create_document_type(
    document_type: DocumentTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document type"""
    
    # Check if user has admin permissions
    if not current_user.has_permission("admin", "EDMS"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check if code already exists
    existing = db.query(DocumentType).filter(
        DocumentType.code == document_type.code
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Document type code already exists")
    
    db_document_type = DocumentType(**document_type.dict())
    db.add(db_document_type)
    db.commit()
    db.refresh(db_document_type)
    
    return db_document_type


@router.put("/types/{type_id}", response_model=DocumentTypeSchema)
async def update_document_type(
    type_id: int,
    document_type: DocumentTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a document type"""
    
    if not current_user.has_permission("admin", "EDMS"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db_document_type = db.query(DocumentType).filter(DocumentType.id == type_id).first()
    if not db_document_type:
        raise HTTPException(status_code=404, detail="Document type not found")
    
    for field, value in document_type.dict(exclude_unset=True).items():
        setattr(db_document_type, field, value)
    
    db.commit()
    db.refresh(db_document_type)
    
    return db_document_type


# Document Category endpoints
@router.get("/categories", response_model=List[DocumentCategorySchema])
async def get_document_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all document categories"""
    categories = db.query(DocumentCategory).filter(
        DocumentCategory.is_active == True
    ).offset(skip).limit(limit).all()
    
    return categories


@router.post("/categories", response_model=DocumentCategorySchema)
async def create_document_category(
    category: DocumentCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document category"""
    
    if not current_user.has_permission("admin", "EDMS"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check if code already exists
    existing = db.query(DocumentCategory).filter(
        DocumentCategory.code == category.code
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Category code already exists")
    
    db_category = DocumentCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category


# Document endpoints
@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search documents with filters"""
    
    document_service = DocumentService(db)
    
    result = document_service.search_documents(
        user_id=current_user.id,
        query=search_request.query,
        document_type_id=search_request.document_type_id,
        category_id=search_request.category_id,
        status=search_request.status,
        author_id=search_request.author_id,
        created_from=search_request.created_from,
        created_to=search_request.created_to,
        page=search_request.page,
        per_page=search_request.per_page
    )
    
    return result


@router.get("/", response_model=DocumentSearchResponse)
async def get_documents(
    query: Optional[str] = None,
    document_type_id: Optional[int] = None,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    author_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents with optional filters"""
    
    search_request = DocumentSearchRequest(
        query=query,
        document_type_id=document_type_id,
        category_id=category_id,
        status=status,
        author_id=author_id,
        page=page,
        per_page=per_page
    )
    
    return await search_documents(search_request, db, current_user)


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID"""
    
    document_service = DocumentService(db)
    document = document_service.get_document(document_id, current_user.id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.post("/upload", response_model=FileUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type_id: int = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    keywords: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    confidentiality_level: str = Form("internal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new document"""
    
    # Check permissions
    if not current_user.has_permission("create_document", "EDMS"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to create documents")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_DOCUMENT_EXTENSIONS)}"
        )
    
    # Check file size
    file_data = await file.read()
    if len(file_data) > settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_DOCUMENT_SIZE_MB}MB"
        )
    
    # Parse keywords and tags
    keywords_list = [k.strip() for k in keywords.split(",")] if keywords else []
    tags_list = [t.strip() for t in tags.split(",")] if tags else []
    
    try:
        document_service = DocumentService(db)
        document = document_service.create_document(
            title=title,
            document_type_id=document_type_id,
            file_data=file_data,
            filename=file.filename,
            user_id=current_user.id,
            description=description,
            category_id=category_id,
            keywords=keywords_list,
            tags=tags_list,
            confidentiality_level=confidentiality_level
        )
        
        return FileUploadResponse(
            success=True,
            message="Document uploaded successfully",
            document_id=document.id,
            document_number=document.document_number
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.put("/{document_id}", response_model=DocumentSchema)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update document metadata"""
    
    document_service = DocumentService(db)
    document = document_service.get_document(document_id, current_user.id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user can edit this document
    if document.author_id != current_user.id and not current_user.has_permission("edit_document", "EDMS"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit this document")
    
    # Update fields
    for field, value in document_update.dict(exclude_unset=True).items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    version_id: Optional[int] = None,
    download_type: str = "original",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download document file"""
    
    document_service = DocumentService(db)
    
    try:
        file_data = document_service.download_document(
            document_id=document_id,
            version_id=version_id,
            user_id=current_user.id,
            download_type=download_type
        )
        
        # Get document info for filename
        document = document_service.get_document(document_id, current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        version = document.current_version
        if version_id:
            version = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id,
                DocumentVersion.document_id == document_id
            ).first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Document version not found")
        
        # Create response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=version.file_mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{document.document_number}_{version.version_number}_{version.file_name}"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")


# Workflow endpoints
@router.post("/{document_id}/start-review", response_model=DocumentWorkflowSchema)
async def start_document_review(
    document_id: int,
    review_request: StartReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start document review workflow"""
    
    document_service = DocumentService(db)
    
    try:
        workflow = document_service.start_review_workflow(
            document_id=document_id,
            reviewer_id=review_request.reviewer_id,
            user_id=current_user.id,
            due_date=review_request.due_date,
            comments=review_request.comments
        )
        
        return workflow
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start review: {str(e)}")


@router.post("/workflows/{workflow_id}/complete-review")
async def complete_document_review(
    workflow_id: int,
    review_request: CompleteReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete document review"""
    
    document_service = DocumentService(db)
    
    try:
        success = document_service.complete_review(
            workflow_id=workflow_id,
            user_id=current_user.id,
            approved=review_request.approved,
            comments=review_request.comments
        )
        
        return {"success": success, "message": "Review completed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete review: {str(e)}")


@router.post("/{document_id}/approve")
async def approve_document(
    document_id: int,
    approve_request: ApproveDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve document for release"""
    
    document_service = DocumentService(db)
    
    try:
        success = document_service.approve_document(
            document_id=document_id,
            user_id=current_user.id,
            effective_date=approve_request.effective_date,
            comments=approve_request.comments
        )
        
        return {"success": success, "message": "Document approved successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a document"""
    
    document_service = DocumentService(db)
    document = document_service.get_document(document_id, current_user.id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check permissions
    if document.author_id != current_user.id and not current_user.has_permission("admin", "EDMS"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete this document")
    
    # Soft delete
    document.is_deleted = True
    db.commit()
    
    return {"success": True, "message": "Document deleted successfully"}