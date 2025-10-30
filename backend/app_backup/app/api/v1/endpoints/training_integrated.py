"""
Training Management System - Integrated Endpoints
Extends existing QMS backend with training functionality
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

# Import existing dependencies
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.audit import AuditLog

# Training-specific imports (will need to be created)
from app.models.training import (
    TrainingProgram, 
    TrainingAssignment, 
    TrainingDocument,
    TrainingModule,
    TrainingPrerequisite
)
from app.schemas.training import (
    TrainingProgramCreate,
    TrainingProgramUpdate, 
    TrainingProgramResponse,
    TrainingAssignmentCreate,
    TrainingAssignmentResponse,
    TrainingDashboardStats,
    TrainingDocumentCreate,
    TrainingDocumentResponse
)
from app.services.training_service_integrated import TrainingServiceIntegrated

router = APIRouter()

# ============================================================================
# TRAINING PROGRAMS ENDPOINTS
# ============================================================================

@router.get("/programs", response_model=List[TrainingProgramResponse])
async def get_training_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by type"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training programs with filtering"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_programs(
        skip=skip, 
        limit=limit, 
        status=status, 
        type=type,
        department_id=department_id
    )

@router.post("/programs", response_model=TrainingProgramResponse)
async def create_training_program(
    program_data: TrainingProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.create_program(program_data)

@router.get("/programs/{program_id}", response_model=TrainingProgramResponse)
async def get_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    program = training_service.get_program_by_id(program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training program not found"
        )
    return program

@router.put("/programs/{program_id}", response_model=TrainingProgramResponse)
async def update_training_program(
    program_id: int,
    program_data: TrainingProgramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.update_program(program_id, program_data)

@router.delete("/programs/{program_id}")
async def delete_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (retire) a training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    training_service.delete_program(program_id)
    return {"message": "Training program deleted successfully"}

# ============================================================================
# TRAINING ASSIGNMENTS ENDPOINTS
# ============================================================================

@router.get("/my-training", response_model=List[TrainingAssignmentResponse])
async def get_my_training_assignments(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's training assignments"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_my_assignments(status=status)

@router.get("/assignments", response_model=List[TrainingAssignmentResponse])
async def get_training_assignments(
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    program_id: Optional[int] = Query(None, description="Filter by program ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training assignments with filtering"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_assignments(
        employee_id=employee_id,
        program_id=program_id,
        status=status,
        department_id=department_id,
        skip=skip,
        limit=limit
    )

@router.post("/assignments", response_model=List[TrainingAssignmentResponse])
async def assign_training(
    assignment_data: TrainingAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign training to employees"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.assign_training(assignment_data)

@router.put("/assignments/{assignment_id}/progress")
async def update_training_progress(
    assignment_id: int,
    progress: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update training progress"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.update_progress(assignment_id, progress)

@router.post("/assignments/{assignment_id}/complete")
async def complete_training(
    assignment_id: int,
    score: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark training as completed"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.complete_training(assignment_id, score)

# ============================================================================
# DASHBOARD AND ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=TrainingDashboardStats)
async def get_training_dashboard(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training dashboard statistics"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_dashboard_stats(department_id=department_id)

@router.get("/dashboard/compliance")
async def get_compliance_report(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    start_date: Optional[datetime] = Query(None, description="Start date for report"),
    end_date: Optional[datetime] = Query(None, description="End date for report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training compliance report"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_compliance_report(
        department_id=department_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/dashboard/employee-summary")
async def get_employee_training_summary(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee training summary"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_employee_training_summary(
        department_id=department_id,
        skip=skip,
        limit=limit
    )

# ============================================================================
# TRAINING DOCUMENTS ENDPOINTS (EDMS Integration)
# ============================================================================

@router.get("/programs/{program_id}/documents", response_model=List[TrainingDocumentResponse])
async def get_program_documents(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents linked to a training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_program_documents(program_id)

@router.post("/programs/{program_id}/documents", response_model=TrainingDocumentResponse)
async def link_document_to_program(
    program_id: int,
    document_data: TrainingDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a document to a training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.link_document(program_id, document_data)

@router.delete("/programs/{program_id}/documents/{document_id}")
async def unlink_document_from_program(
    program_id: int,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unlink a document from a training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    training_service.unlink_document(program_id, document_id)
    return {"message": "Document unlinked successfully"}

# ============================================================================
# TRAINING MODULES ENDPOINTS (Phase 2)
# ============================================================================

@router.get("/programs/{program_id}/modules")
async def get_program_modules(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get modules for a training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_program_modules(program_id)

@router.post("/programs/{program_id}/modules")
async def create_program_module(
    program_id: int,
    module_data: dict,  # Will be properly typed in Phase 2
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training module"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.create_module(program_id, module_data)

# ============================================================================
# EMPLOYEE LOOKUP ENDPOINTS (Integration with existing users)
# ============================================================================

@router.get("/employees")
async def get_employees_for_training(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    role_id: Optional[int] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employees available for training assignment"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_employees_for_assignment(
        department_id=department_id,
        role_id=role_id,
        search=search,
        skip=skip,
        limit=limit
    )

# ============================================================================
# NOTIFICATIONS AND REMINDERS
# ============================================================================

@router.post("/assignments/{assignment_id}/remind")
async def send_training_reminder(
    assignment_id: int,
    message: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a training reminder to employee"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.send_reminder(assignment_id, message)

@router.get("/notifications/overdue")
async def get_overdue_training_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overdue training notifications"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_overdue_notifications()

# ============================================================================
# CERTIFICATES AND TRANSCRIPTS
# ============================================================================

@router.get("/assignments/{assignment_id}/certificate")
async def get_training_certificate(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate/retrieve training certificate"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_certificate(assignment_id)

@router.get("/employees/{employee_id}/transcript")
async def get_training_transcript(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee training transcript"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_training_transcript(employee_id)

# ============================================================================
# SYSTEM CONFIGURATION (Integration with existing system_settings)
# ============================================================================

@router.get("/config")
async def get_training_configuration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get training system configuration"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_system_configuration()

@router.put("/config")
async def update_training_configuration(
    config_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update training system configuration"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.update_system_configuration(config_data)

# ============================================================================
# AUDIT AND HISTORY ENDPOINTS
# ============================================================================

@router.get("/audit/programs/{program_id}")
async def get_program_audit_history(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit history for a training program"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_program_audit_history(program_id)

@router.get("/audit/assignments/{assignment_id}")
async def get_assignment_audit_history(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit history for a training assignment"""
    training_service = TrainingServiceIntegrated(db, current_user)
    return training_service.get_assignment_audit_history(assignment_id)

# ============================================================================
# HEALTH CHECK AND STATUS
# ============================================================================

@router.get("/health")
async def training_health_check(
    db: Session = Depends(get_db)
):
    """Training system health check"""
    try:
        # Test database connectivity
        program_count = db.query(func.count(TrainingProgram.id)).scalar()
        assignment_count = db.query(func.count(TrainingAssignment.id)).scalar()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "connected",
            "statistics": {
                "total_programs": program_count,
                "total_assignments": assignment_count
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Training system health check failed: {str(e)}"
        )