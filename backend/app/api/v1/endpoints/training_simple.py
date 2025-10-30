"""
Simple Training API Endpoints
Working endpoints for training programs
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.training_simple import TrainingProgramSimple, TrainingType, ProgramStatus
from app.schemas.training_simple import (
    TrainingProgramResponse, TrainingProgramCreate, TrainingProgramUpdate
)

router = APIRouter()


@router.get("/programs", response_model=List[TrainingProgramResponse])
async def get_training_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type_filter: Optional[TrainingType] = Query(None, alias="type"),
    status_filter: Optional[ProgramStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all training programs"""
    
    query = db.query(TrainingProgramSimple)
    
    # Apply filters
    if type_filter:
        query = query.filter(TrainingProgramSimple.type == type_filter)
    
    if status_filter:
        query = query.filter(TrainingProgramSimple.status == status_filter)
    else:
        # By default, exclude retired programs
        query = query.filter(TrainingProgramSimple.retired_at.is_(None))
    
    # Get programs
    programs = query.order_by(TrainingProgramSimple.created_at.desc()).offset(skip).limit(limit).all()
    
    return programs


@router.get("/programs/{program_id}", response_model=TrainingProgramResponse)
async def get_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific training program by ID"""
    
    program = db.query(TrainingProgramSimple).filter(TrainingProgramSimple.id == program_id).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
    
    return program


@router.post("/programs", response_model=TrainingProgramResponse)
async def create_training_program(
    program_data: TrainingProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training program"""
    
    # Create the program
    program = TrainingProgramSimple(
        title=program_data.title,
        description=program_data.description,
        type=program_data.type,
        duration=program_data.duration,
        passing_score=program_data.passing_score,
        validity_period=program_data.validity_period,
        department_id=program_data.department_id,
        created_by=program_data.created_by or current_user.id,
        status=ProgramStatus.DRAFT
    )
    
    db.add(program)
    db.commit()
    db.refresh(program)
    
    return program


@router.put("/programs/{program_id}", response_model=TrainingProgramResponse)
async def update_training_program(
    program_id: int,
    program_data: TrainingProgramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing training program"""
    
    program = db.query(TrainingProgramSimple).filter(TrainingProgramSimple.id == program_id).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
    
    # Update fields
    update_data = program_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(program, field, value)
    
    program.updated_by = current_user.id
    
    db.commit()
    db.refresh(program)
    
    return program


@router.get("/dashboard")
async def get_training_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training dashboard statistics"""
    
    total_programs = db.query(TrainingProgramSimple).count()
    active_programs = db.query(TrainingProgramSimple).filter(
        TrainingProgramSimple.status == ProgramStatus.ACTIVE
    ).count()
    draft_programs = db.query(TrainingProgramSimple).filter(
        TrainingProgramSimple.status == ProgramStatus.DRAFT
    ).count()
    
    return {
        "total_programs": total_programs,
        "active_programs": active_programs,
        "draft_programs": draft_programs,
        "last_calculated": datetime.utcnow()
    }