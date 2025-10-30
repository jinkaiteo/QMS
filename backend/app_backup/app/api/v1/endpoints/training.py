"""
Training Management API Endpoints
Phase 4 Implementation - QMS Platform v3.0

REST API endpoints for training programs, employee training,
competency management, and compliance reporting.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.training_service import TrainingService
from app.schemas.training import (
    TrainingProgram, TrainingProgramCreate, TrainingProgramUpdate,
    TrainingSession, TrainingSessionCreate, TrainingSessionUpdate,
    EmployeeTraining, EmployeeTrainingCreate, EmployeeTrainingUpdate,
    Competency, CompetencyCreate, CompetencyUpdate,
    CompetencyAssessment, CompetencyAssessmentCreate, CompetencyAssessmentUpdate,
    TrainingComplianceReport, TrainingDashboard,
    BulkTrainingAssignment, BulkTrainingAssignmentResult
)

router = APIRouter()


def get_training_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TrainingService:
    """Dependency to get training service instance"""
    return TrainingService(db, current_user)


# Training Program Endpoints
@router.post("/programs", response_model=TrainingProgram, status_code=status.HTTP_201_CREATED)
async def create_training_program(
    program_data: TrainingProgramCreate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Create a new training program"""
    return training_service.create_training_program(program_data)


@router.get("/programs", response_model=List[TrainingProgram])
async def list_training_programs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    training_type: Optional[str] = Query(None, description="Filter by training type"),
    active_only: bool = Query(True, description="Show only active programs"),
    training_service: TrainingService = Depends(get_training_service)
):
    """List training programs with optional filtering"""
    return training_service.list_training_programs(
        skip=skip, 
        limit=limit, 
        training_type=training_type, 
        active_only=active_only
    )


@router.get("/programs/{program_id}", response_model=TrainingProgram)
async def get_training_program(
    program_id: int,
    training_service: TrainingService = Depends(get_training_service)
):
    """Get training program by ID"""
    return training_service.get_training_program(program_id)


@router.put("/programs/{program_id}", response_model=TrainingProgram)
async def update_training_program(
    program_id: int,
    program_data: TrainingProgramUpdate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Update training program"""
    return training_service.update_training_program(program_id, program_data)


@router.delete("/programs/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def retire_training_program(
    program_id: int,
    training_service: TrainingService = Depends(get_training_service)
):
    """Retire (soft delete) training program"""
    from datetime import datetime
    update_data = TrainingProgramUpdate(retirement_date=datetime.utcnow())
    training_service.update_training_program(program_id, update_data)


# Employee Training Endpoints
@router.post("/assignments", response_model=EmployeeTraining, status_code=status.HTTP_201_CREATED)
async def assign_training(
    assignment_data: EmployeeTrainingCreate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Assign training to an employee"""
    return training_service.assign_training(assignment_data)


@router.post("/assignments/bulk", response_model=BulkTrainingAssignmentResult)
async def bulk_assign_training(
    bulk_data: BulkTrainingAssignment,
    training_service: TrainingService = Depends(get_training_service)
):
    """Assign training to multiple employees"""
    return training_service.bulk_assign_training(bulk_data)


@router.get("/assignments", response_model=List[EmployeeTraining])
async def list_training_assignments(
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    program_id: Optional[int] = Query(None, description="Filter by program ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    training_service: TrainingService = Depends(get_training_service)
):
    """List training assignments with filtering"""
    return training_service.list_training_assignments(
        employee_id=employee_id,
        program_id=program_id,
        status=status,
        skip=skip,
        limit=limit
    )


@router.get("/assignments/{assignment_id}", response_model=EmployeeTraining)
async def get_training_assignment(
    assignment_id: int,
    training_service: TrainingService = Depends(get_training_service)
):
    """Get training assignment by ID"""
    # Implementation would be added to training_service
    pass


@router.put("/assignments/{assignment_id}", response_model=EmployeeTraining)
async def update_training_assignment(
    assignment_id: int,
    update_data: EmployeeTrainingUpdate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Update training assignment progress"""
    return training_service.update_training_progress(assignment_id, update_data)


# Competency Management Endpoints
@router.post("/competencies", response_model=Competency, status_code=status.HTTP_201_CREATED)
async def create_competency(
    competency_data: CompetencyCreate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Create a new competency"""
    return training_service.create_competency(competency_data)


@router.get("/competencies", response_model=List[Competency])
async def list_competencies(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    training_service: TrainingService = Depends(get_training_service)
):
    """List competencies with optional filtering"""
    # Implementation would be added to training_service
    pass


@router.post("/competencies/assessments", response_model=CompetencyAssessment, status_code=status.HTTP_201_CREATED)
async def create_competency_assessment(
    assessment_data: CompetencyAssessmentCreate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Create a competency assessment"""
    return training_service.assess_competency(assessment_data)


@router.get("/competencies/assessments", response_model=List[CompetencyAssessment])
async def list_competency_assessments(
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    competency_id: Optional[int] = Query(None, description="Filter by competency ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    training_service: TrainingService = Depends(get_training_service)
):
    """List competency assessments with filtering"""
    # Implementation would be added to training_service
    pass


# Reporting Endpoints
@router.get("/reports/compliance", response_model=List[TrainingComplianceReport])
async def get_compliance_report(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    training_service: TrainingService = Depends(get_training_service)
):
    """Generate training compliance report"""
    return training_service.get_training_compliance_report(department_id)


@router.get("/reports/overdue")
async def get_overdue_training_report(
    training_service: TrainingService = Depends(get_training_service)
):
    """Get employees with overdue training"""
    return training_service.get_overdue_training_report()


@router.get("/reports/effectiveness")
async def get_program_effectiveness_report(
    program_id: Optional[int] = Query(None, description="Filter by program ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    training_service: TrainingService = Depends(get_training_service)
):
    """Generate program effectiveness report"""
    # Implementation would be added to training_service
    pass


@router.get("/reports/competency-gaps")
async def get_competency_gap_report(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    role_id: Optional[int] = Query(None, description="Filter by role"),
    training_service: TrainingService = Depends(get_training_service)
):
    """Generate competency gap analysis report"""
    # Implementation would be added to training_service
    pass


# Dashboard Endpoint
@router.get("/dashboard", response_model=TrainingDashboard)
async def get_training_dashboard(
    training_service: TrainingService = Depends(get_training_service)
):
    """Get training management dashboard data"""
    return training_service.get_dashboard_stats()


# Training Sessions (Future Enhancement)
@router.post("/sessions", response_model=TrainingSession, status_code=status.HTTP_201_CREATED)
async def create_training_session(
    session_data: TrainingSessionCreate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Create a training session"""
    # Implementation would be added to training_service
    pass


@router.get("/sessions", response_model=List[TrainingSession])
async def list_training_sessions(
    program_id: Optional[int] = Query(None, description="Filter by program ID"),
    start_date: Optional[str] = Query(None, description="Start date filter"),
    end_date: Optional[str] = Query(None, description="End date filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    training_service: TrainingService = Depends(get_training_service)
):
    """List training sessions with filtering"""
    # Implementation would be added to training_service
    pass


@router.put("/sessions/{session_id}", response_model=TrainingSession)
async def update_training_session(
    session_id: int,
    session_data: TrainingSessionUpdate,
    training_service: TrainingService = Depends(get_training_service)
):
    """Update training session"""
    # Implementation would be added to training_service
    pass


# Employee Self-Service Endpoints
@router.get("/my-training", response_model=List[EmployeeTraining])
async def get_my_training(
    status: Optional[str] = Query(None, description="Filter by status"),
    training_service: TrainingService = Depends(get_training_service)
):
    """Get current user's training assignments"""
    return training_service.get_my_training_assignments(status)


@router.put("/my-training/{assignment_id}/start")
async def start_my_training(
    assignment_id: int,
    training_service: TrainingService = Depends(get_training_service)
):
    """Start a training assignment"""
    from app.schemas.training import TrainingStatus
    update_data = EmployeeTrainingUpdate(
        status=TrainingStatus.IN_PROGRESS,
        start_date=datetime.utcnow()
    )
    return training_service.update_training_progress(assignment_id, update_data)


@router.put("/my-training/{assignment_id}/complete")
async def complete_my_training(
    assignment_id: int,
    score: Optional[float] = Query(None, ge=0, le=100, description="Assessment score"),
    feedback: Optional[str] = Query(None, description="Employee feedback"),
    training_service: TrainingService = Depends(get_training_service)
):
    """Complete a training assignment"""
    from app.schemas.training import TrainingStatus
    from datetime import datetime
    
    update_data = EmployeeTrainingUpdate(
        status=TrainingStatus.COMPLETED,
        completion_date=datetime.utcnow(),
        score=score,
        employee_feedback=feedback,
        pass_fail=score >= 70 if score is not None else True  # Default pass threshold
    )
    return training_service.update_training_progress(assignment_id, update_data)