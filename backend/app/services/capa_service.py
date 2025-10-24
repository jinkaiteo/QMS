# CAPA Service - Phase 3 QRM
# Corrective and Preventive Actions management

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date, timedelta

from app.models.qrm import CAPA, CAPAAction, QualityEvent
from app.models.user import User
from app.core.logging import get_audit_logger


class CAPAService:
    """CAPA management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_logger = get_audit_logger()
    
    def create_capa(
        self,
        title: str,
        description: str,
        capa_type: str,
        problem_statement: str,
        proposed_solution: str,
        owner_id: int,
        target_completion_date: date,
        user_id: int,
        **kwargs
    ) -> CAPA:
        """Create a new CAPA"""
        
        # Generate CAPA number
        capa_number = self._generate_capa_number(capa_type)
        
        # Create CAPA
        capa = CAPA(
            capa_number=capa_number,
            title=title,
            description=description,
            capa_type=capa_type,
            problem_statement=problem_statement,
            proposed_solution=proposed_solution,
            owner_id=owner_id,
            target_completion_date=target_completion_date,
            status="planning",
            priority=kwargs.get('priority', 3),
            action_category=kwargs.get('action_category'),
            source_type=kwargs.get('source_type'),
            source_id=kwargs.get('source_id'),
            quality_event_id=kwargs.get('quality_event_id'),
            investigation_id=kwargs.get('investigation_id'),
            responsible_department_id=kwargs.get('responsible_department_id'),
            assigned_to=kwargs.get('assigned_to'),
            root_cause=kwargs.get('root_cause'),
            implementation_plan=kwargs.get('implementation_plan'),
            success_criteria=kwargs.get('success_criteria'),
            target_start_date=kwargs.get('target_start_date'),
            estimated_cost=kwargs.get('estimated_cost'),
            resources_required=kwargs.get('resources_required'),
            risk_level=kwargs.get('risk_level'),
            verification_method=kwargs.get('verification_method'),
            verification_criteria=kwargs.get('verification_criteria'),
            related_documents=kwargs.get('related_documents', []),
            training_required=kwargs.get('training_required', False)
        )
        
        self.db.add(capa)
        self.db.flush()
        
        # Set verification due date
        if capa.target_completion_date:
            capa.verification_due_date = capa.target_completion_date + timedelta(days=30)
        
        # Log CAPA creation
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="create",
            document_id=capa.id,
            document_number=capa_number,
            details={
                "title": title,
                "capa_type": capa_type,
                "owner_id": owner_id
            }
        )
        
        self.db.commit()
        return capa
    
    def get_capa(self, capa_id: int, user_id: int) -> Optional[CAPA]:
        """Get CAPA by ID with permission check"""
        
        capa = self.db.query(CAPA).filter(
            CAPA.id == capa_id,
            CAPA.is_deleted == False
        ).first()
        
        if not capa:
            return None
        
        # Check permission
        if not self._check_capa_permission(capa, user_id, "read"):
            return None
        
        return capa
    
    def search_capas(
        self,
        user_id: int,
        query: Optional[str] = None,
        capa_type: Optional[str] = None,
        status: Optional[str] = None,
        owner_id: Optional[int] = None,
        department_id: Optional[int] = None,
        due_from: Optional[date] = None,
        due_to: Optional[date] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Search CAPAs with filters"""
        
        base_query = self.db.query(CAPA).filter(
            CAPA.is_deleted == False
        )
        
        # Search
        if query:
            base_query = base_query.filter(
                or_(
                    CAPA.title.ilike(f"%{query}%"),
                    CAPA.description.ilike(f"%{query}%"),
                    CAPA.capa_number.ilike(f"%{query}%")
                )
            )
        
        # Filters
        if capa_type:
            base_query = base_query.filter(CAPA.capa_type == capa_type)
        
        if status:
            base_query = base_query.filter(CAPA.status == status)
        
        if owner_id:
            base_query = base_query.filter(CAPA.owner_id == owner_id)
        
        if department_id:
            base_query = base_query.filter(CAPA.responsible_department_id == department_id)
        
        if due_from:
            base_query = base_query.filter(CAPA.target_completion_date >= due_from)
        
        if due_to:
            base_query = base_query.filter(CAPA.target_completion_date <= due_to)
        
        # Count and paginate
        total = base_query.count()
        capas = base_query.order_by(desc(CAPA.created_at))\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return {
            "items": capas,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    def add_capa_action(
        self,
        capa_id: int,
        title: str,
        description: str,
        assigned_to: int,
        due_date: date,
        user_id: int,
        **kwargs
    ) -> CAPAAction:
        """Add action to CAPA"""
        
        capa = self.get_capa(capa_id, user_id)
        if not capa:
            raise ValueError("CAPA not found or access denied")
        
        if not self._check_capa_permission(capa, user_id, "edit"):
            raise ValueError("Insufficient permissions to edit CAPA")
        
        # Generate action number
        action_count = self.db.query(CAPAAction).filter(
            CAPAAction.capa_id == capa_id
        ).count()
        action_number = f"A{action_count + 1:03d}"
        
        # Create action
        action = CAPAAction(
            capa_id=capa_id,
            action_number=action_number,
            title=title,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            department_id=kwargs.get('department_id'),
            depends_on=kwargs.get('depends_on', []),
            verification_required=kwargs.get('verification_required', False)
        )
        
        self.db.add(action)
        self.db.commit()
        
        return action
    
    def complete_capa_action(
        self,
        action_id: int,
        completion_evidence: str,
        user_id: int
    ) -> bool:
        """Mark CAPA action as completed"""
        
        action = self.db.query(CAPAAction).filter(
            CAPAAction.id == action_id
        ).first()
        
        if not action:
            raise ValueError("CAPA action not found")
        
        # Check permission
        if action.assigned_to != user_id:
            # TODO: Check if user has management permission
            raise ValueError("Only assigned user can complete action")
        
        action.status = "completed"
        action.completed_date = date.today()
        action.completion_percentage = 100
        action.completion_evidence = completion_evidence
        
        # Update CAPA completion percentage
        self._update_capa_completion(action.capa_id)
        
        self.db.commit()
        return True
    
    def approve_capa(
        self,
        capa_id: int,
        approver_id: int,
        comments: Optional[str] = None
    ) -> bool:
        """Approve CAPA for implementation"""
        
        capa = self.db.query(CAPA).filter(CAPA.id == capa_id).first()
        if not capa:
            raise ValueError("CAPA not found")
        
        if capa.status != "planning":
            raise ValueError("CAPA not in planning state")
        
        capa.approved_by = approver_id
        capa.approved_at = datetime.utcnow()
        capa.status = "approved"
        
        # Log approval
        self.audit_logger.log_document_event(
            user_id=approver_id,
            action="approve",
            document_id=capa.id,
            document_number=capa.capa_number,
            details={"comments": comments}
        )
        
        self.db.commit()
        return True
    
    def verify_capa_effectiveness(
        self,
        capa_id: int,
        effectiveness_confirmed: bool,
        verification_comments: str,
        verifier_id: int
    ) -> bool:
        """Verify CAPA effectiveness"""
        
        capa = self.db.query(CAPA).filter(CAPA.id == capa_id).first()
        if not capa:
            raise ValueError("CAPA not found")
        
        if capa.status != "implemented":
            raise ValueError("CAPA must be implemented before verification")
        
        capa.effectiveness_confirmed = effectiveness_confirmed
        capa.verification_comments = verification_comments
        capa.verification_completed_date = date.today()
        
        if effectiveness_confirmed:
            capa.status = "verified"
        else:
            capa.status = "verification_failed"
        
        # Log verification
        self.audit_logger.log_document_event(
            user_id=verifier_id,
            action="verify",
            document_id=capa.id,
            document_number=capa.capa_number,
            details={
                "effectiveness_confirmed": effectiveness_confirmed,
                "comments": verification_comments
            }
        )
        
        self.db.commit()
        return True
    
    def _generate_capa_number(self, capa_type: str) -> str:
        """Generate unique CAPA number"""
        
        # Define prefixes for different CAPA types
        prefixes = {
            "corrective": "CA",
            "preventive": "PA", 
            "improvement": "IA"
        }
        
        prefix = prefixes.get(capa_type, "CA")
        
        # Get next sequence
        last_capa = self.db.query(CAPA)\
            .filter(CAPA.capa_number.like(f"{prefix}%"))\
            .order_by(desc(CAPA.id))\
            .first()
        
        if last_capa:
            try:
                last_seq = int(last_capa.capa_number.split("-")[-1])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}-{seq:06d}"
    
    def _update_capa_completion(self, capa_id: int):
        """Update CAPA completion percentage based on actions"""
        
        actions = self.db.query(CAPAAction).filter(
            CAPAAction.capa_id == capa_id
        ).all()
        
        if not actions:
            return
        
        total_actions = len(actions)
        completed_actions = len([a for a in actions if a.status == "completed"])
        
        completion_percentage = int((completed_actions / total_actions) * 100)
        
        capa = self.db.query(CAPA).filter(CAPA.id == capa_id).first()
        if capa:
            capa.completion_percentage = completion_percentage
            
            # Auto-update status based on completion
            if completion_percentage == 100 and capa.status == "approved":
                capa.status = "implemented"
                capa.actual_completion_date = date.today()
    
    def _check_capa_permission(
        self, 
        capa: CAPA, 
        user_id: int, 
        permission: str
    ) -> bool:
        """Check CAPA permissions"""
        
        # Owner has full access
        if capa.owner_id == user_id:
            return True
        
        # Assignee has access
        if capa.assigned_to == user_id:
            return True
        
        # TODO: Implement role-based permissions
        
        return False