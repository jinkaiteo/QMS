"""
Training Management Service
Phase 4 Implementation - QMS Platform v3.0

Business logic for training programs, employee training records,
competency management, and compliance reporting.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.training import (
    TrainingProgram, TrainingSession, EmployeeTraining, 
    SessionAttendance, Competency, CompetencyAssessment,
    TrainingAssessment, TrainingStatus, CompetencyLevel
)
from app.models.user import User, Role
from app.schemas.training import (
    TrainingProgramCreate, TrainingProgramUpdate,
    TrainingSessionCreate, TrainingSessionUpdate,
    EmployeeTrainingCreate, EmployeeTrainingUpdate,
    CompetencyCreate, CompetencyUpdate,
    CompetencyAssessmentCreate, CompetencyAssessmentUpdate,
    BulkTrainingAssignment
)
from app.services.audit_service import AuditService


class TrainingService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.audit_service = AuditService()

    # Training Program Management
    def create_training_program(self, program_data: TrainingProgramCreate) -> TrainingProgram:
        """Create a new training program"""
        # Check if code already exists
        existing = self.db.query(TrainingProgram).filter(
            TrainingProgram.code == program_data.code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Training program with code '{program_data.code}' already exists"
            )
        
        program = TrainingProgram(**program_data.dict())
        self.db.add(program)
        self.db.commit()
        self.db.refresh(program)
        
        # Log creation
        self.audit_service.log_activity(
            entity_type="TrainingProgram",
            entity_id=program.id,
            action="CREATE",
            details=f"Created training program: {program.title}"
        )
        
        return program

    def get_training_program(self, program_id: int) -> TrainingProgram:
        """Get training program by ID"""
        program = self.db.query(TrainingProgram).filter(
            TrainingProgram.id == program_id
        ).first()
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training program not found"
            )
        return program

    def list_training_programs(
        self, 
        skip: int = 0, 
        limit: int = 100,
        training_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[TrainingProgram]:
        """List training programs with filtering"""
        query = self.db.query(TrainingProgram)
        
        if active_only:
            query = query.filter(
                or_(
                    TrainingProgram.retirement_date.is_(None),
                    TrainingProgram.retirement_date > datetime.utcnow()
                )
            )
        
        if training_type:
            query = query.filter(TrainingProgram.training_type == training_type)
        
        return query.offset(skip).limit(limit).all()

    def update_training_program(
        self, 
        program_id: int, 
        program_data: TrainingProgramUpdate
    ) -> TrainingProgram:
        """Update training program"""
        program = self.get_training_program(program_id)
        
        update_data = program_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(program, field, value)
        
        self.db.commit()
        self.db.refresh(program)
        
        # Log update
        self.audit_service.log_activity(
            entity_type="TrainingProgram",
            entity_id=program.id,
            action="UPDATE",
            details=f"Updated training program: {program.title}"
        )
        
        return program

    # Employee Training Management
    def assign_training(self, assignment_data: EmployeeTrainingCreate) -> EmployeeTraining:
        """Assign training to an employee"""
        # Validate employee exists
        employee = self.db.query(User).filter(User.id == assignment_data.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Validate program exists
        program = self.get_training_program(assignment_data.program_id)
        
        # Check for existing assignment
        existing = self.db.query(EmployeeTraining).filter(
            and_(
                EmployeeTraining.employee_id == assignment_data.employee_id,
                EmployeeTraining.program_id == assignment_data.program_id,
                EmployeeTraining.status.in_([
                    TrainingStatus.NOT_STARTED,
                    TrainingStatus.IN_PROGRESS
                ])
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee already has active assignment for this program"
            )
        
        # Create assignment
        assignment = EmployeeTraining(
            **assignment_data.dict(),
            assigned_by_id=self.current_user.id
        )
        
        # Calculate due date if not provided
        if not assignment.due_date and program.validity_months:
            assignment.due_date = datetime.utcnow() + timedelta(days=30)  # Default 30 days
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        # Log assignment
        self.audit_service.log_activity(
            entity_type="EmployeeTraining",
            entity_id=assignment.id,
            action="ASSIGN",
            details=f"Assigned {program.title} to {employee.username}"
        )
        
        return assignment

    def bulk_assign_training(self, bulk_data: BulkTrainingAssignment) -> Dict[str, Any]:
        """Assign training to multiple employees"""
        program = self.get_training_program(bulk_data.program_id)
        successful = 0
        failed = 0
        errors = []
        
        for employee_id in bulk_data.employee_ids:
            try:
                assignment_data = EmployeeTrainingCreate(
                    employee_id=employee_id,
                    program_id=bulk_data.program_id,
                    due_date=bulk_data.due_date,
                    reason=bulk_data.reason
                )
                self.assign_training(assignment_data)
                successful += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "employee_id": str(employee_id),
                    "error_message": str(e)
                })
        
        return {
            "successful_assignments": successful,
            "failed_assignments": failed,
            "errors": errors
        }

    def update_training_progress(
        self, 
        assignment_id: int, 
        update_data: EmployeeTrainingUpdate
    ) -> EmployeeTraining:
        """Update employee training progress"""
        assignment = self.db.query(EmployeeTraining).filter(
            EmployeeTraining.id == assignment_id
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training assignment not found"
            )
        
        # Validate status transitions
        current_status = assignment.status
        new_status = update_data.status
        
        if new_status and not self._is_valid_status_transition(current_status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {new_status}"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(assignment, field, value)
        
        # Auto-set completion date if status is completed
        if new_status == TrainingStatus.COMPLETED and not assignment.completion_date:
            assignment.completion_date = datetime.utcnow()
        
        # Auto-generate certificate if training is passed
        if (assignment.pass_fail and assignment.status == TrainingStatus.COMPLETED 
            and not assignment.certificate_issued):
            assignment.certificate_issued = True
            assignment.certificate_number = self._generate_certificate_number(assignment)
            assignment.certification_date = datetime.utcnow()
            
            # Set expiry date if program has validity period
            if assignment.program.validity_months:
                assignment.expiry_date = datetime.utcnow() + timedelta(
                    days=assignment.program.validity_months * 30
                )
        
        self.db.commit()
        self.db.refresh(assignment)
        
        # Log progress update
        self.audit_service.log_activity(
            entity_type="EmployeeTraining",
            entity_id=assignment.id,
            action="UPDATE_PROGRESS",
            details=f"Updated training progress: {assignment.status}"
        )
        
        return assignment

    # Competency Management
    def create_competency(self, competency_data: CompetencyCreate) -> Competency:
        """Create a new competency"""
        # Check if code already exists
        existing = self.db.query(Competency).filter(
            Competency.code == competency_data.code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Competency with code '{competency_data.code}' already exists"
            )
        
        competency = Competency(**competency_data.dict())
        self.db.add(competency)
        self.db.commit()
        self.db.refresh(competency)
        
        return competency

    def assess_competency(
        self, 
        assessment_data: CompetencyAssessmentCreate
    ) -> CompetencyAssessment:
        """Create a competency assessment"""
        assessment = CompetencyAssessment(
            **assessment_data.dict(),
            assessor_id=self.current_user.id
        )
        
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        
        # Log assessment
        self.audit_service.log_activity(
            entity_type="CompetencyAssessment",
            entity_id=assessment.id,
            action="CREATE",
            details=f"Assessed competency for employee {assessment.employee_id}"
        )
        
        return assessment

    # Reporting and Analytics
    def get_training_compliance_report(
        self, 
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate training compliance report"""
        query = """
        SELECT 
            u.id as employee_id,
            u.username as employee_name,
            d.name as department,
            COUNT(et.id) as total_assigned,
            SUM(CASE WHEN et.status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN et.status = 'overdue' THEN 1 ELSE 0 END) as overdue,
            SUM(CASE WHEN et.expiry_date BETWEEN NOW() AND NOW() + INTERVAL '30 days' 
                THEN 1 ELSE 0 END) as expiring_soon,
            ROUND(
                (SUM(CASE WHEN et.status = 'completed' THEN 1 ELSE 0 END) * 100.0 / 
                 NULLIF(COUNT(et.id), 0)), 2
            ) as compliance_percentage
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
        LEFT JOIN employee_training et ON u.id = et.employee_id
        WHERE u.is_active = true
        """
        
        if department_id:
            query += f" AND u.department_id = {department_id}"
        
        query += """
        GROUP BY u.id, u.username, d.name
        ORDER BY compliance_percentage DESC
        """
        
        result = self.db.execute(query)
        return [dict(row) for row in result]

    def get_overdue_training_report(self) -> List[Dict[str, Any]]:
        """Get employees with overdue training"""
        overdue_assignments = self.db.query(EmployeeTraining).filter(
            and_(
                EmployeeTraining.due_date < datetime.utcnow(),
                EmployeeTraining.status.in_([
                    TrainingStatus.NOT_STARTED,
                    TrainingStatus.IN_PROGRESS
                ])
            )
        ).all()
        
        return [
            {
                "employee_id": assignment.employee_id,
                "employee_name": assignment.employee.username,
                "program_title": assignment.program.title,
                "due_date": assignment.due_date,
                "days_overdue": (datetime.utcnow() - assignment.due_date).days
            }
            for assignment in overdue_assignments
        ]

    # Helper Methods
    def _is_valid_status_transition(
        self, 
        current: TrainingStatus, 
        new: TrainingStatus
    ) -> bool:
        """Validate training status transitions"""
        valid_transitions = {
            TrainingStatus.NOT_STARTED: [TrainingStatus.IN_PROGRESS, TrainingStatus.COMPLETED],
            TrainingStatus.IN_PROGRESS: [TrainingStatus.COMPLETED, TrainingStatus.NOT_STARTED],
            TrainingStatus.COMPLETED: [TrainingStatus.EXPIRED],
            TrainingStatus.EXPIRED: [TrainingStatus.NOT_STARTED],
            TrainingStatus.OVERDUE: [TrainingStatus.IN_PROGRESS, TrainingStatus.COMPLETED]
        }
        
        return new in valid_transitions.get(current, [])

    def _generate_certificate_number(self, assignment: EmployeeTraining) -> str:
        """Generate unique certificate number"""
        year = datetime.utcnow().year
        program_code = assignment.program.code
        employee_id = assignment.employee_id
        
        return f"CERT-{year}-{program_code}-{employee_id:05d}"

    # API Support Methods
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get training dashboard statistics"""
        try:
            # Count total programs
            total_programs = self.db.query(TrainingProgram).filter(
                TrainingProgram.retirement_date.is_(None)
            ).count()
            
            # Count active assignments
            active_assignments = self.db.query(EmployeeTraining).filter(
                EmployeeTraining.status.in_([
                    TrainingStatus.NOT_STARTED,
                    TrainingStatus.IN_PROGRESS
                ])
            ).count()
            
            # Count completed this month
            current_month = datetime.utcnow().replace(day=1)
            completed_this_month = self.db.query(EmployeeTraining).filter(
                and_(
                    EmployeeTraining.completion_date >= current_month,
                    EmployeeTraining.status == TrainingStatus.COMPLETED
                )
            ).count()
            
            # Count overdue trainings
            overdue_trainings = self.db.query(EmployeeTraining).filter(
                and_(
                    EmployeeTraining.due_date < datetime.utcnow(),
                    EmployeeTraining.status.in_([
                        TrainingStatus.NOT_STARTED,
                        TrainingStatus.IN_PROGRESS
                    ])
                )
            ).count()
            
            # Calculate compliance rate
            total_due = self.db.query(EmployeeTraining).filter(
                EmployeeTraining.due_date <= datetime.utcnow()
            ).count()
            
            completed_on_time = self.db.query(EmployeeTraining).filter(
                and_(
                    EmployeeTraining.due_date <= datetime.utcnow(),
                    EmployeeTraining.status == TrainingStatus.COMPLETED,
                    EmployeeTraining.completion_date <= EmployeeTraining.due_date
                )
            ).count()
            
            compliance_rate = (completed_on_time / total_due * 100) if total_due > 0 else 100
            
            return {
                "totalPrograms": total_programs,
                "activeAssignments": active_assignments,
                "completedThisMonth": completed_this_month,
                "overdueTrainings": overdue_trainings,
                "complianceRate": round(compliance_rate, 1)
            }
            
        except Exception as e:
            # Return fallback data in case of error
            return {
                "totalPrograms": 0,
                "activeAssignments": 0,
                "completedThisMonth": 0,
                "overdueTrainings": 0,
                "complianceRate": 0
            }

    def get_my_training_assignments(self, status: Optional[str] = None) -> List[EmployeeTraining]:
        """Get current user's training assignments"""
        query = self.db.query(EmployeeTraining).filter(
            EmployeeTraining.employee_id == self.current_user.id
        )
        
        if status:
            try:
                training_status = TrainingStatus(status)
                query = query.filter(EmployeeTraining.status == training_status)
            except ValueError:
                # Invalid status, return empty list
                return []
        
        return query.order_by(EmployeeTraining.due_date.asc()).all()

    def list_training_assignments(
        self,
        employee_id: Optional[int] = None,
        program_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[EmployeeTraining]:
        """List training assignments with filtering"""
        query = self.db.query(EmployeeTraining)
        
        if employee_id:
            query = query.filter(EmployeeTraining.employee_id == employee_id)
        
        if program_id:
            query = query.filter(EmployeeTraining.program_id == program_id)
        
        if status:
            try:
                training_status = TrainingStatus(status)
                query = query.filter(EmployeeTraining.status == training_status)
            except ValueError:
                # Invalid status, return empty list
                return []
        
        return query.offset(skip).limit(limit).order_by(
            EmployeeTraining.due_date.asc()
        ).all()