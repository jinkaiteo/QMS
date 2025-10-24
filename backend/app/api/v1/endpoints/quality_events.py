# Quality Events API Endpoints - Phase 3 QRM
# RESTful API for quality event management

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.qrm import QualityEvent, QualityEventType
from app.schemas.qrm import (
    QualityEvent as QualityEventSchema,
    QualityEventList,
    QualityEventCreate,
    QualityEventUpdate,
    QualityEventSearchRequest,
    QualityEventSearchResponse,
    QualityEventType as QualityEventTypeSchema,
    QualityEventTypeCreate,
    AssignInvestigatorRequest,
    UpdateStatusRequest
)
from app.services.quality_event_service import QualityEventService

router = APIRouter()


# Quality Event Type endpoints
@router.get("/types", response_model=List[QualityEventTypeSchema])
async def get_quality_event_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all quality event types"""
    event_types = db.query(QualityEventType).filter(
        QualityEventType.is_active == True
    ).offset(skip).limit(limit).all()
    
    return event_types


@router.post("/types", response_model=QualityEventTypeSchema)
async def create_quality_event_type(
    event_type: QualityEventTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new quality event type"""
    
    # Check if user has admin permissions
    if not current_user.has_permission("admin", "QRM"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check if code already exists
    existing = db.query(QualityEventType).filter(
        QualityEventType.code == event_type.code
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Event type code already exists")
    
    db_event_type = QualityEventType(**event_type.dict())
    db.add(db_event_type)
    db.commit()
    db.refresh(db_event_type)
    
    return db_event_type


# Quality Event endpoints
@router.post("/search", response_model=QualityEventSearchResponse)
async def search_quality_events(
    search_request: QualityEventSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search quality events with filters"""
    
    quality_event_service = QualityEventService(db)
    
    result = quality_event_service.search_quality_events(
        user_id=current_user.id,
        query=search_request.query,
        event_type_id=search_request.event_type_id,
        severity=search_request.severity,
        status=search_request.status,
        reporter_id=search_request.reporter_id,
        department_id=search_request.department_id,
        occurred_from=search_request.occurred_from,
        occurred_to=search_request.occurred_to,
        page=search_request.page,
        per_page=search_request.per_page
    )
    
    return result


@router.get("/", response_model=QualityEventSearchResponse)
async def get_quality_events(
    query: Optional[str] = None,
    event_type_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    reporter_id: Optional[int] = None,
    department_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality events with optional filters"""
    
    search_request = QualityEventSearchRequest(
        query=query,
        event_type_id=event_type_id,
        severity=severity,
        status=status,
        reporter_id=reporter_id,
        department_id=department_id,
        page=page,
        per_page=per_page
    )
    
    return await search_quality_events(search_request, db, current_user)


@router.get("/{event_id}", response_model=QualityEventSchema)
async def get_quality_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific quality event by ID"""
    
    quality_event_service = QualityEventService(db)
    quality_event = quality_event_service.get_quality_event(event_id, current_user.id)
    
    if not quality_event:
        raise HTTPException(status_code=404, detail="Quality event not found")
    
    return quality_event


@router.post("/", response_model=QualityEventSchema)
async def create_quality_event(
    quality_event: QualityEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new quality event"""
    
    # Check permissions
    if not current_user.has_permission("create_quality_event", "QRM"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to create quality events")
    
    try:
        quality_event_service = QualityEventService(db)
        
        # Convert Pydantic model to dict, excluding None values
        event_data = quality_event.dict(exclude_unset=True)
        
        # Extract required fields
        title = event_data.pop('title')
        description = event_data.pop('description')
        event_type_id = event_data.pop('event_type_id')
        severity = event_data.pop('severity')
        occurred_at = event_data.pop('occurred_at')
        
        # Create quality event
        db_quality_event = quality_event_service.create_quality_event(
            title=title,
            description=description,
            event_type_id=event_type_id,
            severity=severity,
            occurred_at=occurred_at,
            reporter_id=current_user.id,
            **event_data  # Pass remaining fields as kwargs
        )
        
        return db_quality_event
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create quality event: {str(e)}")


@router.put("/{event_id}", response_model=QualityEventSchema)
async def update_quality_event(
    event_id: int,
    quality_event_update: QualityEventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update quality event"""
    
    quality_event_service = QualityEventService(db)
    quality_event = quality_event_service.get_quality_event(event_id, current_user.id)
    
    if not quality_event:
        raise HTTPException(status_code=404, detail="Quality event not found")
    
    # Check if user can edit this quality event
    if (quality_event.reporter_id != current_user.id and 
        not current_user.has_permission("edit_quality_event", "QRM")):
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit this quality event")
    
    # Update fields
    for field, value in quality_event_update.dict(exclude_unset=True).items():
        setattr(quality_event, field, value)
    
    db.commit()
    db.refresh(quality_event)
    
    return quality_event


@router.post("/{event_id}/assign-investigator")
async def assign_investigator(
    event_id: int,
    assign_request: AssignInvestigatorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign investigator to quality event"""
    
    quality_event_service = QualityEventService(db)
    
    try:
        success = quality_event_service.assign_investigator(
            event_id=event_id,
            investigator_id=assign_request.investigator_id,
            user_id=current_user.id
        )
        
        return {"success": success, "message": "Investigator assigned successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign investigator: {str(e)}")


@router.post("/{event_id}/update-status")
async def update_quality_event_status(
    event_id: int,
    status_request: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update quality event status"""
    
    quality_event_service = QualityEventService(db)
    
    try:
        success = quality_event_service.update_event_status(
            event_id=event_id,
            new_status=status_request.status,
            user_id=current_user.id,
            comments=status_request.comments
        )
        
        return {"success": success, "message": "Status updated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.delete("/{event_id}")
async def delete_quality_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a quality event"""
    
    quality_event_service = QualityEventService(db)
    quality_event = quality_event_service.get_quality_event(event_id, current_user.id)
    
    if not quality_event:
        raise HTTPException(status_code=404, detail="Quality event not found")
    
    # Check permissions
    if (quality_event.reporter_id != current_user.id and 
        not current_user.has_permission("admin", "QRM")):
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete this quality event")
    
    # Soft delete
    quality_event.is_deleted = True
    db.commit()
    
    return {"success": True, "message": "Quality event deleted successfully"}


# Dashboard and analytics endpoints
@router.get("/analytics/summary")
async def get_quality_events_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality events analytics summary"""
    
    from sqlalchemy import func
    
    # Basic counts by status
    status_counts = db.query(
        QualityEvent.status,
        func.count(QualityEvent.id)
    ).filter(
        QualityEvent.is_deleted == False
    ).group_by(QualityEvent.status).all()
    
    # Severity counts
    severity_counts = db.query(
        QualityEvent.severity,
        func.count(QualityEvent.id)
    ).filter(
        QualityEvent.is_deleted == False
    ).group_by(QualityEvent.severity).all()
    
    # Overdue investigations
    from datetime import date
    overdue_investigations = db.query(func.count(QualityEvent.id)).filter(
        QualityEvent.is_deleted == False,
        QualityEvent.status == "investigating",
        QualityEvent.investigation_due_date < date.today()
    ).scalar()
    
    return {
        "status_counts": dict(status_counts),
        "severity_counts": dict(severity_counts),
        "overdue_investigations": overdue_investigations,
        "total_events": sum(count for _, count in status_counts)
    }