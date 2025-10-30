"""
Document Version Control API Endpoints
Version management, lifecycle, and controlled numbering
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.edms import Document
from app.services.document_version_service import DocumentVersionService

router = APIRouter()


@router.post("/create-version/{document_id}")
async def create_new_version(
    document_id: int,
    file: UploadFile = File(...),
    change_summary: str = Form(...),
    version_type: str = Form("minor"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new version of an existing document"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        
        # Read file data
        file_data = await file.read()
        
        # Create new version
        new_version = version_service.create_new_version(
            document_id=document_id,
            file_data=file_data,
            filename=file.filename,
            change_summary=change_summary,
            version_type=version_type
        )
        
        return {
            "success": True,
            "version_id": new_version.id,
            "version_number": new_version.version_number,
            "file_path": new_version.file_path,
            "message": f"New version {new_version.version_number} created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{document_id}")
async def get_version_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete version history for a document"""
    
    version_service = DocumentVersionService(db, current_user)
    history = version_service.get_version_history(document_id)
    
    return {
        "document_id": document_id,
        "version_count": len(history),
        "versions": history
    }


@router.get("/compare/{document_id}")
async def compare_versions(
    document_id: int,
    version1: str,
    version2: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare two versions of a document"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        comparison = version_service.compare_versions(document_id, version1, version2)
        
        return comparison
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/supersede")
async def supersede_document(
    old_document_id: int,
    new_document_id: int,
    supersession_reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a document as superseded by another document"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        
        success = version_service.supersede_document(
            old_document_id=old_document_id,
            new_document_id=new_document_id,
            supersession_reason=supersession_reason
        )
        
        return {
            "success": success,
            "message": f"Document {old_document_id} superseded by {new_document_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/retire/{document_id}")
async def retire_document(
    document_id: int,
    retirement_reason: str,
    effective_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retire a document from active use"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        
        success = version_service.retire_document(
            document_id=document_id,
            retirement_reason=retirement_reason,
            effective_date=effective_date
        )
        
        return {
            "success": success,
            "message": f"Document {document_id} retired successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/archive/{document_id}")
async def archive_document(
    document_id: int,
    archive_reason: str,
    retention_years: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a document for long-term storage"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        
        success = version_service.archive_document(
            document_id=document_id,
            archive_reason=archive_reason,
            retention_years=retention_years
        )
        
        return {
            "success": success,
            "message": f"Document {document_id} archived successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/genealogy/{document_id}")
async def get_document_genealogy(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document family tree (superseded/supersedes relationships)"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        genealogy = version_service.get_document_genealogy(document_id)
        
        return genealogy
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/generate-number")
async def generate_document_number(
    document_type_id: int,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a controlled document number"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        
        document_number = version_service.generate_document_number(
            document_type_id=document_type_id,
            category_id=category_id
        )
        
        return {
            "document_number": document_number,
            "document_type_id": document_type_id,
            "category_id": category_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lifecycle/metrics")
async def get_lifecycle_metrics(
    document_type_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document lifecycle metrics and statistics"""
    
    version_service = DocumentVersionService(db, current_user)
    metrics = version_service.get_lifecycle_metrics(document_type_id)
    
    return metrics


@router.get("/lifecycle/dashboard")
async def get_lifecycle_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document lifecycle dashboard data"""
    
    version_service = DocumentVersionService(db, current_user)
    
    # Get overall metrics
    overall_metrics = version_service.get_lifecycle_metrics()
    
    # Get documents needing attention
    documents_query = db.query(Document)
    
    # Documents needing review
    review_due = documents_query.filter(
        Document.review_due_date <= datetime.utcnow()
    ).limit(10).all()
    
    # Recently updated documents
    recent_updates = documents_query.filter(
        Document.updated_at >= datetime.utcnow() - timedelta(days=7)
    ).order_by(Document.updated_at.desc()).limit(10).all()
    
    # Format for response
    review_due_list = [{
        "id": doc.id,
        "title": doc.title,
        "document_number": doc.document_number,
        "review_due_date": doc.review_due_date,
        "current_version": doc.current_version
    } for doc in review_due]
    
    recent_updates_list = [{
        "id": doc.id,
        "title": doc.title,
        "document_number": doc.document_number,
        "updated_at": doc.updated_at,
        "current_version": doc.current_version
    } for doc in recent_updates]
    
    return {
        "metrics": overall_metrics,
        "documents_needing_review": review_due_list,
        "recent_updates": recent_updates_list,
        "summary": {
            "total_documents": overall_metrics["total_documents"],
            "active_documents": overall_metrics["status_distribution"].get("approved", 0) + 
                              overall_metrics["status_distribution"].get("published", 0),
            "documents_needing_review": len(review_due_list),
            "average_versions": overall_metrics["version_statistics"]["average_versions_per_document"]
        }
    }


@router.post("/bulk-retire")
async def bulk_retire_documents(
    document_ids: List[int],
    retirement_reason: str,
    effective_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retire multiple documents in bulk"""
    
    try:
        version_service = DocumentVersionService(db, current_user)
        
        results = []
        for document_id in document_ids:
            try:
                success = version_service.retire_document(
                    document_id=document_id,
                    retirement_reason=retirement_reason,
                    effective_date=effective_date
                )
                results.append({
                    "document_id": document_id,
                    "success": success,
                    "message": "Retired successfully"
                })
            except Exception as e:
                results.append({
                    "document_id": document_id,
                    "success": False,
                    "message": str(e)
                })
        
        successful_retirements = len([r for r in results if r["success"]])
        
        return {
            "total_processed": len(document_ids),
            "successful_retirements": successful_retirements,
            "failed_retirements": len(document_ids) - successful_retirements,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))