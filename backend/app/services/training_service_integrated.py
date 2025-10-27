"""
Training Management Service - Integrated Version
Works with existing QMS database structure and user management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from fastapi import HTTPException, status

# Import existing models
from app.models.user import User
from app.models.audit import AuditLog
# from app.models.department import Department  # Adjust import based on your structure

# Training models (to be created)
from app.models.training import (
    TrainingProgram, 
    TrainingAssignment, 
    TrainingDocument,
    TrainingModule,
    TrainingPrerequisite,
    TrainingType,
    ProgramStatus, 
    AssignmentStatus,
    DocumentType,
    DocumentCategory
)

# Training schemas (to be created)
from app.schemas.training import (
    TrainingProgramCreate,
    TrainingProgramUpdate,
    TrainingAssignmentCreate,
    TrainingDocumentCreate
)


class TrainingServiceIntegrated:
    """
    Integrated Training Management Service
    
    This service integrates with the existing QMS database structure:
    - Uses existing users table for employee management
    - Integrates with existing departments for organizational structure
    - Leverages existing audit_logs for change tracking
    - Connects with existing system_settings for configuration
    """
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    # ============================================================================
    # TRAINING PROGRAMS MANAGEMENT
    # ============================================================================
    
    def get_programs(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        type: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> List[TrainingProgram]:
        """Get training programs with filtering"""
        query = self.db.query(TrainingProgram).options(
            joinedload(TrainingProgram.created_by_user),
            joinedload(TrainingProgram.department)
        )
        
        # Apply filters
        if status:
            query = query.filter(TrainingProgram.status == status)
        if type:
            query = query.filter(TrainingProgram.type == type)
        if department_id:
            query = query.filter(TrainingProgram.department_id == department_id)
        
        # Filter out retired programs unless specifically requested
        if status != 'archived':
            query = query.filter(TrainingProgram.retired_at.is_(None))
        
        return query.offset(skip).limit(limit).order_by(desc(TrainingProgram.created_at)).all()
    
    def get_program_by_id(self, program_id: int) -> Optional[TrainingProgram]:
        """Get a specific training program by ID"""
        return self.db.query(TrainingProgram).options(
            joinedload(TrainingProgram.created_by_user),
            joinedload(TrainingProgram.department),
            joinedload(TrainingProgram.documents),
            joinedload(TrainingProgram.modules)
        ).filter(TrainingProgram.id == program_id).first()
    
    def create_program(self, program_data: TrainingProgramCreate) -> TrainingProgram:
        """Create a new training program"""
        # Validate department exists (if specified)
        if program_data.department_id:
            department = self.db.query(Department).filter(
                Department.id == program_data.department_id
            ).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department not found"
                )
        
        # Create training program
        db_program = TrainingProgram(
            title=program_data.title,
            description=program_data.description,
            type=program_data.type,
            duration=program_data.duration,
            passing_score=program_data.passing_score,
            validity_period=program_data.validity_period,
            department_id=program_data.department_id,
            created_by=self.current_user.id,
            status=ProgramStatus.DRAFT  # Start as draft
        )
        
        self.db.add(db_program)
        self.db.commit()
        self.db.refresh(db_program)
        
        # Log creation in audit trail
        self._log_audit(
            table_name="training_programs",
            record_id=db_program.id,
            action="CREATE",
            new_values=self._program_to_dict(db_program),
            user_id=self.current_user.id
        )
        
        return db_program
    
    def update_program(self, program_id: int, program_data: TrainingProgramUpdate) -> TrainingProgram:
        """Update a training program"""
        db_program = self.get_program_by_id(program_id)
        if not db_program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training program not found"
            )
        
        # Check permissions
        if not self._can_modify_program(db_program):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to modify this program"
            )
        
        # Store old values for audit
        old_values = self._program_to_dict(db_program)
        
        # Update fields
        update_data = program_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_program, field):
                setattr(db_program, field, value)
        
        db_program.updated_by = self.current_user.id
        db_program.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_program)
        
        # Log update in audit trail
        self._log_audit(
            table_name="training_programs",
            record_id=db_program.id,
            action="UPDATE",
            old_values=old_values,
            new_values=self._program_to_dict(db_program),
            user_id=self.current_user.id
        )
        
        return db_program
    
    def delete_program(self, program_id: int) -> None:
        """Delete (retire) a training program"""
        db_program = self.get_program_by_id(program_id)
        if not db_program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training program not found"
            )
        
        # Check permissions
        if not self._can_modify_program(db_program):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete this program"
            )
        
        # Check if program has active assignments
        active_assignments = self.db.query(TrainingAssignment).filter(
            and_(
                TrainingAssignment.program_id == program_id,
                TrainingAssignment.status.in_([
                    AssignmentStatus.ASSIGNED,
                    AssignmentStatus.NOT_STARTED,
                    AssignmentStatus.IN_PROGRESS
                ])
            )
        ).count()
        
        if active_assignments > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete program with {active_assignments} active assignments"
            )
        
        # Soft delete (retire)
        old_values = self._program_to_dict(db_program)
        db_program.status = ProgramStatus.ARCHIVED
        db_program.retired_at = datetime.utcnow()
        db_program.retirement_reason = "Deleted by user"
        db_program.updated_by = self.current_user.id
        
        self.db.commit()
        
        # Log deletion in audit trail
        self._log_audit(
            table_name="training_programs",
            record_id=db_program.id,
            action="DELETE",
            old_values=old_values,
            new_values=self._program_to_dict(db_program),
            user_id=self.current_user.id
        )
    
    # ============================================================================
    # TRAINING ASSIGNMENTS MANAGEMENT
    # ============================================================================
    
    def get_my_assignments(self, status: Optional[str] = None) -> List[TrainingAssignment]:
        """Get current user's training assignments"""
        query = self.db.query(TrainingAssignment).options(
            joinedload(TrainingAssignment.program),
            joinedload(TrainingAssignment.assigned_by_user)
        ).filter(TrainingAssignment.employee_id == self.current_user.id)
        
        if status:
            query = query.filter(TrainingAssignment.status == status)
        
        return query.order_by(asc(TrainingAssignment.due_date)).all()
    
    def get_assignments(
        self,
        employee_id: Optional[int] = None,
        program_id: Optional[int] = None,
        status: Optional[str] = None,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TrainingAssignment]:
        """Get training assignments with filtering"""
        query = self.db.query(TrainingAssignment).options(
            joinedload(TrainingAssignment.program),
            joinedload(TrainingAssignment.employee),
            joinedload(TrainingAssignment.assigned_by_user)
        )
        
        # Apply filters
        if employee_id:
            query = query.filter(TrainingAssignment.employee_id == employee_id)
        if program_id:
            query = query.filter(TrainingAssignment.program_id == program_id)
        if status:
            query = query.filter(TrainingAssignment.status == status)
        if department_id:
            # Join with users to filter by department
            query = query.join(User, TrainingAssignment.employee_id == User.id)
            query = query.filter(User.department_id == department_id)
        
        return query.offset(skip).limit(limit).order_by(desc(TrainingAssignment.assigned_at)).all()
    
    def assign_training(self, assignment_data: TrainingAssignmentCreate) -> List[TrainingAssignment]:
        """Assign training to employees"""
        # Validate program exists
        program = self.get_program_by_id(assignment_data.program_id)
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training program not found"
            )
        
        # Validate program is active
        if program.status != ProgramStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign inactive training program"
            )
        
        assignments = []
        
        for employee_id in assignment_data.employee_ids:
            # Validate employee exists
            employee = self.db.query(User).filter(User.id == employee_id).first()
            if not employee:
                continue  # Skip invalid employees
            
            # Check if assignment already exists
            existing = self.db.query(TrainingAssignment).filter(
                and_(
                    TrainingAssignment.program_id == assignment_data.program_id,
                    TrainingAssignment.employee_id == employee_id
                )
            ).first()
            
            if existing:
                continue  # Skip if already assigned
            
            # Create assignment
            db_assignment = TrainingAssignment(
                program_id=assignment_data.program_id,
                employee_id=employee_id,
                assigned_by=self.current_user.id,
                due_date=assignment_data.due_date,
                notes=assignment_data.notes,
                status=AssignmentStatus.ASSIGNED
            )
            
            self.db.add(db_assignment)
            assignments.append(db_assignment)
        
        self.db.commit()
        
        # Refresh all assignments to get related data
        for assignment in assignments:
            self.db.refresh(assignment)
            
            # Log assignment in audit trail
            self._log_audit(
                table_name="training_assignments",
                record_id=assignment.id,
                action="CREATE",
                new_values=self._assignment_to_dict(assignment),
                user_id=self.current_user.id
            )
        
        return assignments
    
    def update_progress(self, assignment_id: int, progress: int) -> TrainingAssignment:
        """Update training progress"""
        if progress < 0 or progress > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Progress must be between 0 and 100"
            )
        
        assignment = self.db.query(TrainingAssignment).filter(
            TrainingAssignment.id == assignment_id
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training assignment not found"
            )
        
        # Check permissions (employee can update their own progress)
        if assignment.employee_id != self.current_user.id and not self._is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        old_values = self._assignment_to_dict(assignment)
        
        # Update progress and status
        assignment.progress = progress
        
        if progress > 0 and assignment.status == AssignmentStatus.ASSIGNED:
            assignment.status = AssignmentStatus.IN_PROGRESS
            assignment.started_at = datetime.utcnow()
        
        assignment.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Log progress update
        self._log_audit(
            table_name="training_assignments",
            record_id=assignment.id,
            action="UPDATE",
            old_values=old_values,
            new_values=self._assignment_to_dict(assignment),
            user_id=self.current_user.id
        )
        
        return assignment
    
    def complete_training(self, assignment_id: int, score: Optional[int] = None) -> TrainingAssignment:
        """Mark training as completed"""
        assignment = self.db.query(TrainingAssignment).filter(
            TrainingAssignment.id == assignment_id
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training assignment not found"
            )
        
        # Check permissions
        if assignment.employee_id != self.current_user.id and not self._is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Validate score if provided
        if score is not None and (score < 0 or score > 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Score must be between 0 and 100"
            )
        
        old_values = self._assignment_to_dict(assignment)
        
        # Mark as completed
        assignment.status = AssignmentStatus.COMPLETED
        assignment.progress = 100
        assignment.completed_at = datetime.utcnow()
        assignment.score = score
        assignment.updated_at = datetime.utcnow()
        
        # Check if passing score was met
        if score is not None and assignment.program.passing_score:
            if score < assignment.program.passing_score:
                assignment.status = AssignmentStatus.FAILED
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Log completion
        self._log_audit(
            table_name="training_assignments",
            record_id=assignment.id,
            action="COMPLETE",
            old_values=old_values,
            new_values=self._assignment_to_dict(assignment),
            user_id=self.current_user.id
        )
        
        return assignment
    
    # ============================================================================
    # DASHBOARD AND ANALYTICS
    # ============================================================================
    
    def get_dashboard_stats(self, department_id: Optional[int] = None) -> Dict[str, Any]:
        """Get training dashboard statistics"""
        # Base queries
        programs_query = self.db.query(TrainingProgram)
        assignments_query = self.db.query(TrainingAssignment)
        
        # Apply department filter if specified
        if department_id:
            programs_query = programs_query.filter(TrainingProgram.department_id == department_id)
            assignments_query = assignments_query.join(User, TrainingAssignment.employee_id == User.id)
            assignments_query = assignments_query.filter(User.department_id == department_id)
        
        # Calculate statistics
        total_programs = programs_query.filter(TrainingProgram.status == ProgramStatus.ACTIVE).count()
        
        active_assignments = assignments_query.filter(
            TrainingAssignment.status.in_([
                AssignmentStatus.ASSIGNED,
                AssignmentStatus.NOT_STARTED,
                AssignmentStatus.IN_PROGRESS
            ])
        ).count()
        
        # Monthly completions
        current_month = datetime.utcnow().replace(day=1)
        completed_this_month = assignments_query.filter(
            and_(
                TrainingAssignment.status == AssignmentStatus.COMPLETED,
                TrainingAssignment.completed_at >= current_month
            )
        ).count()
        
        # Overdue trainings
        overdue_trainings = assignments_query.filter(
            and_(
                TrainingAssignment.status.in_([
                    AssignmentStatus.ASSIGNED,
                    AssignmentStatus.NOT_STARTED,
                    AssignmentStatus.IN_PROGRESS
                ]),
                TrainingAssignment.due_date < datetime.utcnow()
            )
        ).count()
        
        # Compliance rate calculation
        total_due = assignments_query.filter(
            TrainingAssignment.due_date <= datetime.utcnow()
        ).count()
        
        completed_on_time = assignments_query.filter(
            and_(
                TrainingAssignment.status == AssignmentStatus.COMPLETED,
                TrainingAssignment.due_date <= datetime.utcnow(),
                TrainingAssignment.completed_at <= TrainingAssignment.due_date
            )
        ).count()
        
        compliance_rate = (completed_on_time / total_due * 100) if total_due > 0 else 100.0
        
        return {
            "totalPrograms": total_programs,
            "activeAssignments": active_assignments,
            "completedThisMonth": completed_this_month,
            "overdueTrainings": overdue_trainings,
            "complianceRate": round(compliance_rate, 1)
        }
    
    # ============================================================================
    # EMPLOYEE MANAGEMENT (Integration with existing users)
    # ============================================================================
    
    def get_employees_for_assignment(
        self,
        department_id: Optional[int] = None,
        role_id: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get employees available for training assignment"""
        query = self.db.query(User).filter(User.is_active == True)
        
        # Apply filters
        if department_id:
            query = query.filter(User.department_id == department_id)
        if role_id:
            # Assuming you have a user_roles relationship
            query = query.join(UserRole).filter(UserRole.role_id == role_id)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        
        employees = query.offset(skip).limit(limit).all()
        
        # Format for frontend compatibility
        result = []
        for employee in employees:
            department_name = employee.department.name if employee.department else "Unknown"
            
            result.append({
                "id": employee.id,
                "name": f"{employee.first_name or ''} {employee.last_name or ''}".strip() or employee.username,
                "email": employee.email,
                "department": department_name,
                "jobRole": getattr(employee, 'job_title', 'Employee')  # Adjust based on your User model
            })
        
        return result
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _can_modify_program(self, program: TrainingProgram) -> bool:
        """Check if current user can modify a training program"""
        # Admin can modify any program
        if self._is_admin():
            return True
        
        # Program creator can modify their own programs
        if program.created_by == self.current_user.id:
            return True
        
        # Department managers can modify programs in their department
        if self._is_department_manager() and program.department_id == self.current_user.department_id:
            return True
        
        return False
    
    def _is_admin(self) -> bool:
        """Check if current user is an admin"""
        # Adjust based on your role system
        return any(role.name in ['admin', 'super_admin'] for role in self.current_user.roles)
    
    def _is_department_manager(self) -> bool:
        """Check if current user is a department manager"""
        # Adjust based on your role system
        return any(role.name in ['department_manager', 'manager'] for role in self.current_user.roles)
    
    def _log_audit(
        self,
        table_name: str,
        record_id: int,
        action: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        user_id: Optional[int] = None
    ) -> None:
        """Log action to existing audit_logs table"""
        audit_log = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id or self.current_user.id,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(audit_log)
        # Note: Don't commit here, let the calling method handle the transaction
    
    def _program_to_dict(self, program: TrainingProgram) -> Dict[str, Any]:
        """Convert training program to dictionary for audit logging"""
        return {
            "id": program.id,
            "title": program.title,
            "description": program.description,
            "type": program.type.value if program.type else None,
            "duration": program.duration,
            "passing_score": program.passing_score,
            "validity_period": program.validity_period,
            "status": program.status.value if program.status else None,
            "department_id": program.department_id,
            "created_by": program.created_by,
            "updated_by": program.updated_by
        }
    
    def _assignment_to_dict(self, assignment: TrainingAssignment) -> Dict[str, Any]:
        """Convert training assignment to dictionary for audit logging"""
        return {
            "id": assignment.id,
            "program_id": assignment.program_id,
            "employee_id": assignment.employee_id,
            "assigned_by": assignment.assigned_by,
            "status": assignment.status.value if assignment.status else None,
            "progress": assignment.progress,
            "score": assignment.score,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "completed_at": assignment.completed_at.isoformat() if assignment.completed_at else None
        }