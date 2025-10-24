# Quality Event Service - Phase 3 QRM
# Quality event management business logic

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date

from app.models.qrm import QualityEvent, QualityEventType, QualityInvestigation
from app.models.user import User
from app.models.base import Department
from app.core.logging import get_audit_logger
from app.core.config import settings


class QualityEventService:
    """Quality event management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_logger = get_audit_logger()
    
    def create_quality_event(
        self,
        title: str,
        description: str,
        event_type_id: int,
        severity: str,
        occurred_at: datetime,
        reporter_id: int,
        **kwargs
    ) -> QualityEvent:
        """Create a new quality event"""
        
        # Generate event number
        event_number = self._generate_event_number(event_type_id)
        
        # Create quality event
        quality_event = QualityEvent(
            event_number=event_number,
            title=title,
            description=description,
            event_type_id=event_type_id,
            severity=severity,
            occurred_at=occurred_at,
            reporter_id=reporter_id,
            discovered_at=datetime.utcnow(),
            status="open",
            priority=kwargs.get('priority', 3),
            source=kwargs.get('source'),
            location=kwargs.get('location'),
            department_id=kwargs.get('department_id'),
            product_affected=kwargs.get('product_affected'),
            batch_lot_numbers=kwargs.get('batch_lot_numbers', []),
            processes_affected=kwargs.get('processes_affected', []),
            patient_safety_impact=kwargs.get('patient_safety_impact', False),
            product_quality_impact=kwargs.get('product_quality_impact', False),
            regulatory_impact=kwargs.get('regulatory_impact', False),
            business_impact_severity=kwargs.get('business_impact_severity'),
            estimated_cost=kwargs.get('estimated_cost'),
            investigation_required=kwargs.get('investigation_required', True),
            capa_required=kwargs.get('capa_required', False),
            regulatory_reporting_required=kwargs.get('regulatory_reporting_required', False)
        )
        
        self.db.add(quality_event)
        self.db.flush()
        
        # Set investigation due date based on severity
        if quality_event.investigation_required:
            quality_event.investigation_due_date = self._calculate_investigation_due_date(severity)
        
        # Log the event creation
        self.audit_logger.log_document_event(
            user_id=reporter_id,
            action="create",
            document_id=quality_event.id,
            document_number=event_number,
            details={
                "title": title,
                "severity": severity,
                "event_type_id": event_type_id
            }
        )
        
        self.db.commit()
        return quality_event
    
    def get_quality_event(self, event_id: int, user_id: int) -> Optional[QualityEvent]:
        """Get quality event by ID with permission check"""
        
        quality_event = self.db.query(QualityEvent).filter(
            QualityEvent.id == event_id,
            QualityEvent.is_deleted == False
        ).first()
        
        if not quality_event:
            return None
        
        # Check read permission (basic implementation)
        if not self._check_event_permission(quality_event, user_id, "read"):
            return None
        
        return quality_event
    
    def search_quality_events(
        self,
        user_id: int,
        query: Optional[str] = None,
        event_type_id: Optional[int] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        reporter_id: Optional[int] = None,
        department_id: Optional[int] = None,
        occurred_from: Optional[date] = None,
        occurred_to: Optional[date] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Search quality events with filters and pagination"""
        
        base_query = self.db.query(QualityEvent).filter(
            QualityEvent.is_deleted == False
        )
        
        # Full-text search
        if query:
            base_query = base_query.filter(
                or_(
                    QualityEvent.title.ilike(f"%{query}%"),
                    QualityEvent.description.ilike(f"%{query}%"),
                    QualityEvent.event_number.ilike(f"%{query}%")
                )
            )
        
        # Apply filters
        if event_type_id:
            base_query = base_query.filter(QualityEvent.event_type_id == event_type_id)
        
        if severity:
            base_query = base_query.filter(QualityEvent.severity == severity)
        
        if status:
            base_query = base_query.filter(QualityEvent.status == status)
        
        if reporter_id:
            base_query = base_query.filter(QualityEvent.reporter_id == reporter_id)
        
        if department_id:
            base_query = base_query.filter(QualityEvent.department_id == department_id)
        
        if occurred_from:
            base_query = base_query.filter(QualityEvent.occurred_at >= occurred_from)
        
        if occurred_to:
            base_query = base_query.filter(QualityEvent.occurred_at <= occurred_to)
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and ordering
        quality_events = base_query.order_by(desc(QualityEvent.created_at))\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return {
            "items": quality_events,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    def assign_investigator(
        self,
        event_id: int,
        investigator_id: int,
        user_id: int
    ) -> bool:
        """Assign investigator to quality event"""
        
        quality_event = self.get_quality_event(event_id, user_id)
        if not quality_event:
            raise ValueError("Quality event not found or access denied")
        
        if not self._check_event_permission(quality_event, user_id, "assign"):
            raise ValueError("Insufficient permissions to assign investigator")
        
        quality_event.investigator_id = investigator_id
        quality_event.status = "investigating"
        
        # Log the assignment
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="update",
            document_id=quality_event.id,
            document_number=quality_event.event_number,
            details={
                "action": "assign_investigator",
                "investigator_id": investigator_id
            }
        )
        
        self.db.commit()
        return True
    
    def update_event_status(
        self,
        event_id: int,
        new_status: str,
        user_id: int,
        comments: Optional[str] = None
    ) -> bool:
        """Update quality event status"""
        
        quality_event = self.get_quality_event(event_id, user_id)
        if not quality_event:
            raise ValueError("Quality event not found or access denied")
        
        if not self._check_event_permission(quality_event, user_id, "update"):
            raise ValueError("Insufficient permissions to update event")
        
        old_status = quality_event.status
        quality_event.status = new_status
        
        # Handle status-specific logic
        if new_status == "closed":
            quality_event.actual_closure_date = date.today()
        
        # Log the status change
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="update",
            document_id=quality_event.id,
            document_number=quality_event.event_number,
            details={
                "action": "status_change",
                "old_status": old_status,
                "new_status": new_status,
                "comments": comments
            }
        )
        
        self.db.commit()
        return True
    
    def _generate_event_number(self, event_type_id: int) -> str:
        """Generate unique quality event number"""
        
        event_type = self.db.query(QualityEventType).get(event_type_id)
        if not event_type:
            raise ValueError("Invalid event type")
        
        prefix = f"QE-{event_type.code}"
        
        # Get next sequence number
        last_event = self.db.query(QualityEvent)\
            .filter(QualityEvent.event_number.like(f"{prefix}%"))\
            .order_by(desc(QualityEvent.id))\
            .first()
        
        if last_event:
            try:
                last_seq = int(last_event.event_number.split("-")[-1])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}-{seq:06d}"
    
    def _calculate_investigation_due_date(self, severity: str) -> date:
        """Calculate investigation due date based on severity"""
        
        from datetime import timedelta
        
        today = date.today()
        
        # Define investigation timeframes based on severity
        timeframes = {
            "critical": 1,    # 1 day
            "major": 3,       # 3 days
            "minor": 7,       # 7 days
            "informational": 14  # 14 days
        }
        
        days = timeframes.get(severity.lower(), 7)  # Default to 7 days
        return today + timedelta(days=days)
    
    def _check_event_permission(
        self, 
        quality_event: QualityEvent, 
        user_id: int, 
        permission: str
    ) -> bool:
        """Check if user has permission for quality event operation"""
        
        # Reporter always has access to their own events
        if quality_event.reporter_id == user_id:
            return True
        
        # Assignee has access
        if quality_event.assigned_to == user_id:
            return True
        
        # Investigator has access
        if quality_event.investigator_id == user_id:
            return True
        
        # TODO: Implement more sophisticated permission checking
        # based on roles, department access, etc.
        
        return False