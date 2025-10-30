"""
Document Workflow Service
Manages pharmaceutical document approval workflows
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.edms import Document, DocumentType
from app.models.document_workflow import (
    DocumentWorkflowTemplate, WorkflowStepTemplate, DocumentWorkflowInstance,
    DocumentWorkflowStep, DocumentSignature, DocumentComment, DocumentNotification,
    WorkflowStatus, ApprovalAction, SignatureType
)
from app.services.notification_service import notification_service


class DocumentWorkflowService:
    """Service for managing document workflows"""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def initiate_workflow(
        self, 
        document_id: int, 
        template_id: Optional[int] = None,
        custom_reviewers: Optional[List[int]] = None,
        custom_approvers: Optional[List[int]] = None,
        due_date: Optional[datetime] = None
    ) -> DocumentWorkflowInstance:
        """Initiate a workflow for a document"""
        
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        # Get or create workflow template
        if template_id:
            template = self.db.query(DocumentWorkflowTemplate).filter(
                DocumentWorkflowTemplate.id == template_id
            ).first()
        else:
            # Use default template for document type
            template = self.db.query(DocumentWorkflowTemplate).filter(
                DocumentWorkflowTemplate.document_type_id == document.document_type_id,
                DocumentWorkflowTemplate.is_active == True
            ).first()
        
        if not template:
            # Create basic workflow if no template exists
            return self._create_basic_workflow(document_id, due_date)
        
        # Calculate due date if not provided
        if not due_date:
            total_days = template.review_days + template.approval_days
            due_date = datetime.utcnow() + timedelta(days=total_days)
        
        # Create workflow instance
        workflow_instance = DocumentWorkflowInstance(
            document_id=document_id,
            template_id=template.id,
            workflow_name=f"{template.name} - {document.title}",
            initiated_by_id=self.current_user.id,
            due_date=due_date,
            status=WorkflowStatus.IN_PROGRESS
        )
        
        self.db.add(workflow_instance)
        self.db.flush()  # Get the ID
        
        # Create workflow steps
        step_templates = self.db.query(WorkflowStepTemplate).filter(
            WorkflowStepTemplate.template_id == template.id
        ).order_by(WorkflowStepTemplate.step_order).all()
        
        for step_template in step_templates:
            # Determine assignee
            assignee_id = self._determine_step_assignee(
                step_template, 
                document, 
                custom_reviewers if step_template.step_type == "review" else custom_approvers
            )
            
            step_due_date = datetime.utcnow() + timedelta(days=step_template.days_to_complete)
            
            workflow_step = DocumentWorkflowStep(
                workflow_instance_id=workflow_instance.id,
                step_order=step_template.step_order,
                step_name=step_template.step_name,
                step_type=step_template.step_type,
                assigned_to_id=assignee_id,
                assigned_by_id=self.current_user.id,
                assigned_at=datetime.utcnow() if step_template.step_order == 1 else None,
                due_date=step_due_date,
                status=WorkflowStatus.PENDING if step_template.step_order == 1 else WorkflowStatus.PENDING
            )
            
            self.db.add(workflow_step)
        
        self.db.commit()
        self.db.refresh(workflow_instance)
        
        # Send initial notifications
        self._send_workflow_notifications(workflow_instance, "initiated")
        
        return workflow_instance
    
    def complete_workflow_step(
        self,
        step_id: int,
        action: ApprovalAction,
        comments: Optional[str] = None,
        signature_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Complete a workflow step"""
        
        step = self.db.query(DocumentWorkflowStep).filter(
            DocumentWorkflowStep.id == step_id
        ).first()
        
        if not step:
            raise ValueError("Workflow step not found")
        
        # Verify user can complete this step
        if step.assigned_to_id != self.current_user.id:
            raise ValueError("User not authorized to complete this step")
        
        if step.status == WorkflowStatus.COMPLETED:
            raise ValueError("Step already completed")
        
        # Update step
        step.completed_by_id = self.current_user.id
        step.completed_at = datetime.utcnow()
        step.status = WorkflowStatus.COMPLETED
        step.action_taken = action
        step.comments = comments
        
        # Create electronic signature if provided
        if signature_data:
            signature = self._create_electronic_signature(step, signature_data)
            self.db.add(signature)
        
        # Determine next steps based on action
        if action == ApprovalAction.APPROVE:
            self._advance_workflow(step.workflow_instance_id)
        elif action == ApprovalAction.REJECT:
            self._reject_workflow(step.workflow_instance_id, comments)
        elif action == ApprovalAction.RETURN_FOR_REVISION:
            self._return_for_revision(step.workflow_instance_id, comments)
        
        self.db.commit()
        
        # Send notifications
        self._send_step_completion_notifications(step, action)
        
        return True
    
    def add_comment(
        self,
        document_id: int,
        comment_text: str,
        comment_type: str = "general",
        workflow_step_id: Optional[int] = None,
        page_number: Optional[int] = None,
        section_reference: Optional[str] = None
    ) -> DocumentComment:
        """Add a comment to a document"""
        
        comment = DocumentComment(
            document_id=document_id,
            workflow_step_id=workflow_step_id,
            comment_text=comment_text,
            comment_type=comment_type,
            page_number=page_number,
            section_reference=section_reference,
            created_by_id=self.current_user.id
        )
        
        self.db.add(comment)
        self.db.commit()
        
        # Notify relevant users
        self._send_comment_notifications(comment)
        
        return comment
    
    def get_user_tasks(
        self,
        user_id: Optional[int] = None,
        status: Optional[WorkflowStatus] = None,
        overdue_only: bool = False
    ) -> List[DocumentWorkflowStep]:
        """Get workflow tasks for a user"""
        
        target_user_id = user_id or self.current_user.id
        
        query = self.db.query(DocumentWorkflowStep).filter(
            DocumentWorkflowStep.assigned_to_id == target_user_id
        )
        
        if status:
            query = query.filter(DocumentWorkflowStep.status == status)
        else:
            query = query.filter(DocumentWorkflowStep.status.in_([
                WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS
            ]))
        
        if overdue_only:
            query = query.filter(
                DocumentWorkflowStep.due_date < datetime.utcnow()
            )
        
        return query.order_by(DocumentWorkflowStep.due_date.asc()).all()
    
    def get_workflow_status(self, document_id: int) -> Dict[str, Any]:
        """Get workflow status for a document"""
        
        workflow = self.db.query(DocumentWorkflowInstance).filter(
            DocumentWorkflowInstance.document_id == document_id
        ).first()
        
        if not workflow:
            return {"status": "no_workflow", "steps": []}
        
        steps = self.db.query(DocumentWorkflowStep).filter(
            DocumentWorkflowStep.workflow_instance_id == workflow.id
        ).order_by(DocumentWorkflowStep.step_order).all()
        
        step_data = []
        for step in steps:
            step_info = {
                "id": step.id,
                "step_name": step.step_name,
                "step_type": step.step_type,
                "status": step.status,
                "assigned_to": step.assigned_to.username if step.assigned_to else None,
                "due_date": step.due_date,
                "completed_at": step.completed_at,
                "completed_by": step.completed_by.username if step.completed_by else None,
                "action_taken": step.action_taken,
                "comments": step.comments
            }
            step_data.append(step_info)
        
        return {
            "workflow_id": workflow.id,
            "status": workflow.status,
            "current_step": workflow.current_step,
            "initiated_by": workflow.initiator.username,
            "initiated_at": workflow.initiated_at,
            "due_date": workflow.due_date,
            "steps": step_data
        }
    
    def delegate_task(
        self,
        step_id: int,
        delegate_to_id: int,
        reason: str
    ) -> bool:
        """Delegate a workflow task to another user"""
        
        step = self.db.query(DocumentWorkflowStep).filter(
            DocumentWorkflowStep.id == step_id
        ).first()
        
        if not step:
            raise ValueError("Workflow step not found")
        
        if step.assigned_to_id != self.current_user.id:
            raise ValueError("User not authorized to delegate this step")
        
        # Update step assignment
        step.delegated_to_id = step.assigned_to_id
        step.assigned_to_id = delegate_to_id
        step.delegation_reason = reason
        
        self.db.commit()
        
        # Send delegation notification
        self._send_delegation_notification(step)
        
        return True
    
    # Private helper methods
    
    def _create_basic_workflow(self, document_id: int, due_date: Optional[datetime]) -> DocumentWorkflowInstance:
        """Create a basic workflow when no template exists"""
        
        if not due_date:
            due_date = datetime.utcnow() + timedelta(days=7)
        
        workflow_instance = DocumentWorkflowInstance(
            document_id=document_id,
            workflow_name="Basic Document Review",
            initiated_by_id=self.current_user.id,
            due_date=due_date,
            status=WorkflowStatus.IN_PROGRESS
        )
        
        self.db.add(workflow_instance)
        self.db.flush()
        
        # Create a simple review step
        review_step = DocumentWorkflowStep(
            workflow_instance_id=workflow_instance.id,
            step_order=1,
            step_name="Document Review",
            step_type="review",
            assigned_to_id=self.current_user.id,  # Assign to initiator for now
            assigned_by_id=self.current_user.id,
            assigned_at=datetime.utcnow(),
            due_date=due_date,
            status=WorkflowStatus.PENDING
        )
        
        self.db.add(review_step)
        return workflow_instance
    
    def _determine_step_assignee(
        self,
        step_template: WorkflowStepTemplate,
        document: Document,
        custom_assignees: Optional[List[int]]
    ) -> Optional[int]:
        """Determine who should be assigned to a workflow step"""
        
        if custom_assignees and len(custom_assignees) > 0:
            return custom_assignees[0]  # Use first custom assignee
        
        if step_template.user_id:
            return step_template.user_id
        
        # Add logic here for role-based or department-based assignment
        # For now, assign to the document creator
        return document.created_by_id
    
    def _advance_workflow(self, workflow_instance_id: int):
        """Advance workflow to next step"""
        
        workflow = self.db.query(DocumentWorkflowInstance).filter(
            DocumentWorkflowInstance.id == workflow_instance_id
        ).first()
        
        # Find next pending step
        next_step = self.db.query(DocumentWorkflowStep).filter(
            DocumentWorkflowStep.workflow_instance_id == workflow_instance_id,
            DocumentWorkflowStep.status == WorkflowStatus.PENDING,
            DocumentWorkflowStep.step_order > workflow.current_step
        ).order_by(DocumentWorkflowStep.step_order).first()
        
        if next_step:
            # Activate next step
            next_step.assigned_at = datetime.utcnow()
            workflow.current_step = next_step.step_order
        else:
            # Workflow complete
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
    
    def _reject_workflow(self, workflow_instance_id: int, reason: str):
        """Reject the workflow"""
        
        workflow = self.db.query(DocumentWorkflowInstance).filter(
            DocumentWorkflowInstance.id == workflow_instance_id
        ).first()
        
        workflow.status = WorkflowStatus.REJECTED
        workflow.completed_at = datetime.utcnow()
        workflow.comments = reason
    
    def _return_for_revision(self, workflow_instance_id: int, reason: str):
        """Return document for revision"""
        
        workflow = self.db.query(DocumentWorkflowInstance).filter(
            DocumentWorkflowInstance.id == workflow_instance_id
        ).first()
        
        # Reset workflow to beginning
        workflow.current_step = 1
        workflow.comments = reason
        
        # Reset all steps to pending
        self.db.query(DocumentWorkflowStep).filter(
            DocumentWorkflowStep.workflow_instance_id == workflow_instance_id
        ).update({
            "status": WorkflowStatus.PENDING,
            "completed_at": None,
            "completed_by_id": None,
            "action_taken": None
        })
    
    def _create_electronic_signature(
        self,
        step: DocumentWorkflowStep,
        signature_data: Dict[str, Any]
    ) -> DocumentSignature:
        """Create an electronic signature"""
        
        import hashlib
        import json
        
        # Create signature hash
        signature_content = {
            "user_id": self.current_user.id,
            "document_id": step.workflow_instance.document_id,
            "step_id": step.id,
            "timestamp": datetime.utcnow().isoformat(),
            "meaning": signature_data.get("meaning", "Approved"),
            "method": signature_data.get("method", "password")
        }
        
        signature_hash = hashlib.sha256(
            json.dumps(signature_content, sort_keys=True).encode()
        ).hexdigest()
        
        signature = DocumentSignature(
            document_id=step.workflow_instance.document_id,
            workflow_step_id=step.id,
            signer_id=self.current_user.id,
            signature_type=SignatureType.APPROVAL,
            signature_meaning=signature_data.get("meaning", "Approved"),
            signature_hash=signature_hash,
            signature_method=signature_data.get("method", "password"),
            ip_address=signature_data.get("ip_address"),
            user_agent=signature_data.get("user_agent")
        )
        
        return signature
    
    def _send_workflow_notifications(self, workflow: DocumentWorkflowInstance, event_type: str):
        """Send notifications for workflow events"""
        # Implementation would integrate with notification service
        pass
    
    def _send_step_completion_notifications(self, step: DocumentWorkflowStep, action: ApprovalAction):
        """Send notifications when a step is completed"""
        # Implementation would notify relevant users
        pass
    
    def _send_comment_notifications(self, comment: DocumentComment):
        """Send notifications for new comments"""
        # Implementation would notify document stakeholders
        pass
    
    def _send_delegation_notification(self, step: DocumentWorkflowStep):
        """Send notification for task delegation"""
        # Implementation would notify the new assignee
        pass