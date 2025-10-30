"""
Training Management API Endpoints - Database Integrated
Corrected endpoints that work with the actual database schema
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.training_integrated import (
    TrainingProgram, TrainingAssignment, TrainingModule, 
    TrainingPrerequisite, EmployeeTrainingSummary,
    TrainingType, ProgramStatus, AssignmentStatus
)
from app.schemas.training_integrated import (
    TrainingProgramResponse, TrainingProgramCreate, TrainingProgramUpdate,
    TrainingAssignmentResponse, TrainingAssignmentCreate, TrainingAssignmentUpdate,
    TrainingModuleResponse, TrainingModuleCreate, TrainingModuleUpdate,
    BulkAssignmentRequest, BulkAssignmentResponse,
    TrainingProgramFilter, TrainingAssignmentFilter,
    TrainingProgramListResponse, TrainingAssignmentListResponse,
    EmployeeTrainingSummaryResponse, TrainingDashboardResponse
)

router = APIRouter()


# Training Programs endpoints
@router.get("/programs", response_model=List[TrainingProgramResponse])
async def get_training_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type_filter: Optional[TrainingType] = Query(None, alias="type"),
    status_filter: Optional[ProgramStatus] = Query(None, alias="status"),
    department_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all training programs with optional filtering"""
    
    query = db.query(TrainingProgram)
    
    # Apply filters
    if type_filter:
        query = query.filter(TrainingProgram.type == type_filter)
    
    if status_filter:
        query = query.filter(TrainingProgram.status == status_filter)
    else:
        # By default, exclude retired programs unless specifically requested
        query = query.filter(TrainingProgram.retired_at.is_(None))
    
    if department_id:
        query = query.filter(TrainingProgram.department_id == department_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (TrainingProgram.title.ilike(search_pattern)) |
            (TrainingProgram.description.ilike(search_pattern))
        )
    
    # Order by creation date (newest first) and apply pagination
    programs = query.order_by(TrainingProgram.created_at.desc()).offset(skip).limit(limit).all()
    
    return programs


@router.get("/programs/{program_id}", response_model=TrainingProgramResponse)
async def get_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific training program by ID"""
    
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    
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
    
    # Set creator if not specified
    if not program_data.created_by:
        program_data.created_by = current_user.id
    
    # Create the program
    program = TrainingProgram(
        title=program_data.title,
        description=program_data.description,
        type=program_data.type,
        duration=program_data.duration,
        passing_score=program_data.passing_score,
        validity_period=program_data.validity_period,
        department_id=program_data.department_id,
        created_by=program_data.created_by,
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
    
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
    
    # Update fields
    update_data = program_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "retirement_reason" and value:
            # If setting retirement reason, also set retired_at
            program.retired_at = datetime.utcnow()
        setattr(program, field, value)
    
    program.updated_by = current_user.id
    
    db.commit()
    db.refresh(program)
    
    return program


@router.delete("/programs/{program_id}")
async def retire_training_program(
    program_id: int,
    retirement_reason: str = Query(..., description="Reason for retirement"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retire a training program (soft delete)"""
    
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
    
    program.status = ProgramStatus.RETIRED
    program.retired_at = datetime.utcnow()
    program.retirement_reason = retirement_reason
    program.updated_by = current_user.id
    
    db.commit()
    
    return {"message": "Training program retired successfully"}


# Training Assignments endpoints
@router.get("/assignments", response_model=List[TrainingAssignmentResponse])
async def get_training_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    program_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    status_filter: Optional[AssignmentStatus] = Query(None, alias="status"),
    overdue_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training assignments with optional filtering"""
    
    query = db.query(TrainingAssignment)
    
    # Apply filters
    if program_id:
        query = query.filter(TrainingAssignment.program_id == program_id)
    
    if employee_id:
        query = query.filter(TrainingAssignment.employee_id == employee_id)
    
    if status_filter:
        query = query.filter(TrainingAssignment.status == status_filter)
    
    if overdue_only:
        query = query.filter(
            TrainingAssignment.due_date < datetime.utcnow(),
            TrainingAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS])
        )
    
    # Order by due date and apply pagination
    assignments = query.order_by(TrainingAssignment.due_date.asc()).offset(skip).limit(limit).all()
    
    return assignments


@router.post("/assignments", response_model=TrainingAssignmentResponse)
async def create_training_assignment(
    assignment_data: TrainingAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training assignment"""
    
    # Verify the program exists
    program = db.query(TrainingProgram).filter(TrainingProgram.id == assignment_data.program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
    
    # Verify the employee exists
    employee = db.query(User).filter(User.id == assignment_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if assignment already exists
    existing = db.query(TrainingAssignment).filter(
        TrainingAssignment.program_id == assignment_data.program_id,
        TrainingAssignment.employee_id == assignment_data.employee_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Training assignment already exists for this employee")
    
    # Create the assignment
    assignment = TrainingAssignment(
        program_id=assignment_data.program_id,
        employee_id=assignment_data.employee_id,
        assigned_by_id=assignment_data.assigned_by_id or current_user.id,
        due_date=assignment_data.due_date,
        notes=assignment_data.notes,
        status=AssignmentStatus.ASSIGNED
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    return assignment


# Dashboard endpoint
@router.get("/dashboard", response_model=TrainingDashboardResponse)
async def get_training_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training dashboard statistics"""
    
    # Calculate statistics
    total_programs = db.query(TrainingProgram).count()
    active_programs = db.query(TrainingProgram).filter(TrainingProgram.status == ProgramStatus.ACTIVE).count()
    total_assignments = db.query(TrainingAssignment).count()
    completed_assignments = db.query(TrainingAssignment).filter(TrainingAssignment.status == AssignmentStatus.COMPLETED).count()
    overdue_assignments = db.query(TrainingAssignment).filter(
        TrainingAssignment.due_date < datetime.utcnow(),
        TrainingAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS])
    ).count()
    
    overall_compliance_rate = 0
    if total_assignments > 0:
        overall_compliance_rate = round((completed_assignments / total_assignments) * 100)
    
    return TrainingDashboardResponse(
        total_programs=total_programs,
        active_programs=active_programs,
        total_assignments=total_assignments,
        completed_assignments=completed_assignments,
        overdue_assignments=overdue_assignments,
        overall_compliance_rate=overall_compliance_rate,
        last_calculated=datetime.utcnow()
    )