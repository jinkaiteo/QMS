# CAPA API Endpoints - Phase 3 QRM
# RESTful API for CAPA management

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.qrm import CAPA, CAPAAction
from app.schemas.qrm import (
    CAPA as CAPASchema,
    CAPACreate,
    CAPAUpdate,
    CAPASearchRequest,
    CAPASearchResponse,
    CAPAAction as CAPAActionSchema,
    CAPAActionCreate,
    CAPAActionUpdate,
    ApproveCAPARequest,
    VerifyEffectivenessRequest,
    CompleteActionRequest
)
from app.services.capa_service import CAPAService

router = APIRouter()


# CAPA endpoints
@router.post("/search", response_model=CAPASearchResponse)
async def search_capas(
    search_request: CAPASearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search CAPAs with filters"""
    
    capa_service = CAPAService(db)
    
    result = capa_service.search_capas(
        user_id=current_user.id,
        query=search_request.query,
        capa_type=search_request.capa_type,
        status=search_request.status,
        owner_id=search_request.owner_id,
        department_id=search_request.department_id,
        due_from=search_request.due_from,
        due_to=search_request.due_to,
        page=search_request.page,
        per_page=search_request.per_page
    )
    
    return result


@router.get("/", response_model=CAPASearchResponse)
async def get_capas(
    query: Optional[str] = None,
    capa_type: Optional[str] = None,
    status: Optional[str] = None,
    owner_id: Optional[int] = None,
    department_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get CAPAs with optional filters"""
    
    search_request = CAPASearchRequest(
        query=query,
        capa_type=capa_type,
        status=status,
        owner_id=owner_id,
        department_id=department_id,
        page=page,
        per_page=per_page
    )
    
    return await search_capas(search_request, db, current_user)


@router.get("/{capa_id}", response_model=CAPASchema)
async def get_capa(
    capa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific CAPA by ID"""
    
    capa_service = CAPAService(db)
    capa = capa_service.get_capa(capa_id, current_user.id)
    
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    
    return capa


@router.post("/", response_model=CAPASchema)
async def create_capa(
    capa: CAPACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new CAPA"""
    
    # Check permissions
    if not current_user.has_permission("create_capa", "QRM"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to create CAPAs")
    
    try:
        capa_service = CAPAService(db)
        
        # Convert Pydantic model to dict
        capa_data = capa.dict(exclude_unset=True)
        
        # Extract required fields
        title = capa_data.pop('title')
        description = capa_data.pop('description')
        capa_type = capa_data.pop('capa_type')
        problem_statement = capa_data.pop('problem_statement')
        proposed_solution = capa_data.pop('proposed_solution')
        owner_id = capa_data.pop('owner_id')
        target_completion_date = capa_data.pop('target_completion_date')
        
        # Create CAPA
        db_capa = capa_service.create_capa(
            title=title,
            description=description,
            capa_type=capa_type,
            problem_statement=problem_statement,
            proposed_solution=proposed_solution,
            owner_id=owner_id,
            target_completion_date=target_completion_date,
            user_id=current_user.id,
            **capa_data  # Pass remaining fields as kwargs
        )
        
        return db_capa
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create CAPA: {str(e)}")


@router.put("/{capa_id}", response_model=CAPASchema)
async def update_capa(
    capa_id: int,
    capa_update: CAPAUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update CAPA"""
    
    capa_service = CAPAService(db)
    capa = capa_service.get_capa(capa_id, current_user.id)
    
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    
    # Check if user can edit this CAPA
    if (capa.owner_id != current_user.id and 
        not current_user.has_permission("edit_capa", "QRM")):
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit this CAPA")
    
    # Update fields
    for field, value in capa_update.dict(exclude_unset=True).items():
        setattr(capa, field, value)
    
    db.commit()
    db.refresh(capa)
    
    return capa


@router.post("/{capa_id}/approve")
async def approve_capa(
    capa_id: int,
    approve_request: ApproveCAPARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve CAPA for implementation"""
    
    # Check permissions
    if not current_user.has_permission("approve_capa", "QRM"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to approve CAPAs")
    
    capa_service = CAPAService(db)
    
    try:
        success = capa_service.approve_capa(
            capa_id=capa_id,
            approver_id=current_user.id,
            comments=approve_request.comments
        )
        
        return {"success": success, "message": "CAPA approved successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve CAPA: {str(e)}")


@router.post("/{capa_id}/verify-effectiveness")
async def verify_capa_effectiveness(
    capa_id: int,
    verify_request: VerifyEffectivenessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify CAPA effectiveness"""
    
    # Check permissions
    if not current_user.has_permission("verify_capa", "QRM"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to verify CAPAs")
    
    capa_service = CAPAService(db)
    
    try:
        success = capa_service.verify_capa_effectiveness(
            capa_id=capa_id,
            effectiveness_confirmed=verify_request.effectiveness_confirmed,
            verification_comments=verify_request.verification_comments,
            verifier_id=current_user.id
        )
        
        return {"success": success, "message": "CAPA effectiveness verified successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify CAPA: {str(e)}")


# CAPA Actions endpoints
@router.get("/{capa_id}/actions", response_model=List[CAPAActionSchema])
async def get_capa_actions(
    capa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all actions for a CAPA"""
    
    capa_service = CAPAService(db)
    capa = capa_service.get_capa(capa_id, current_user.id)
    
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    
    actions = db.query(CAPAAction).filter(
        CAPAAction.capa_id == capa_id
    ).order_by(CAPAAction.action_number).all()
    
    return actions


@router.post("/{capa_id}/actions", response_model=CAPAActionSchema)
async def create_capa_action(
    capa_id: int,
    action: CAPAActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add action to CAPA"""
    
    capa_service = CAPAService(db)
    
    try:
        # Convert Pydantic model to dict
        action_data = action.dict(exclude_unset=True)
        
        # Extract required fields
        title = action_data.pop('title')
        assigned_to = action_data.pop('assigned_to')
        due_date = action_data.pop('due_date')
        description = action_data.get('description')
        
        # Create action
        db_action = capa_service.add_capa_action(
            capa_id=capa_id,
            title=title,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            user_id=current_user.id,
            **action_data  # Pass remaining fields as kwargs
        )
        
        return db_action
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create CAPA action: {str(e)}")


@router.put("/actions/{action_id}", response_model=CAPAActionSchema)
async def update_capa_action(
    action_id: int,
    action_update: CAPAActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update CAPA action"""
    
    action = db.query(CAPAAction).filter(CAPAAction.id == action_id).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="CAPA action not found")
    
    # Check permissions (only assigned user or CAPA owner can update)
    if (action.assigned_to != current_user.id and 
        action.capa.owner_id != current_user.id and
        not current_user.has_permission("edit_capa", "QRM")):
        raise HTTPException(status_code=403, detail="Insufficient permissions to update this action")
    
    # Update fields
    for field, value in action_update.dict(exclude_unset=True).items():
        setattr(action, field, value)
    
    db.commit()
    db.refresh(action)
    
    return action


@router.post("/actions/{action_id}/complete")
async def complete_capa_action(
    action_id: int,
    complete_request: CompleteActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark CAPA action as completed"""
    
    capa_service = CAPAService(db)
    
    try:
        success = capa_service.complete_capa_action(
            action_id=action_id,
            completion_evidence=complete_request.completion_evidence,
            user_id=current_user.id
        )
        
        return {"success": success, "message": "CAPA action completed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete CAPA action: {str(e)}")


@router.delete("/{capa_id}")
async def delete_capa(
    capa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a CAPA"""
    
    capa_service = CAPAService(db)
    capa = capa_service.get_capa(capa_id, current_user.id)
    
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    
    # Check permissions
    if (capa.owner_id != current_user.id and 
        not current_user.has_permission("admin", "QRM")):
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete this CAPA")
    
    # Soft delete
    capa.is_deleted = True
    db.commit()
    
    return {"success": True, "message": "CAPA deleted successfully"}


# Analytics endpoints
@router.get("/analytics/summary")
async def get_capas_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get CAPA analytics summary"""
    
    from sqlalchemy import func
    from datetime import date
    
    # Status counts
    status_counts = db.query(
        CAPA.status,
        func.count(CAPA.id)
    ).filter(
        CAPA.is_deleted == False
    ).group_by(CAPA.status).all()
    
    # Type counts
    type_counts = db.query(
        CAPA.capa_type,
        func.count(CAPA.id)
    ).filter(
        CAPA.is_deleted == False
    ).group_by(CAPA.capa_type).all()
    
    # Overdue CAPAs
    overdue_capas = db.query(func.count(CAPA.id)).filter(
        CAPA.is_deleted == False,
        CAPA.status.in_(["approved", "in_progress"]),
        CAPA.target_completion_date < date.today()
    ).scalar()
    
    # Completion percentage average
    avg_completion = db.query(func.avg(CAPA.completion_percentage)).filter(
        CAPA.is_deleted == False,
        CAPA.status.in_(["approved", "in_progress"])
    ).scalar()
    
    return {
        "status_counts": dict(status_counts),
        "type_counts": dict(type_counts),
        "overdue_capas": overdue_capas,
        "average_completion": float(avg_completion) if avg_completion else 0,
        "total_capas": sum(count for _, count in status_counts)
    }