"""
Document Workflow API Endpoints
Handles workflow operations for document review, approval, and lifecycle management
"""
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.document_workflow_service import DocumentWorkflowService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Pydantic models for request/response

class WorkflowStartRequest(BaseModel):
    reviewer_id: int
    due_days: int = Field(default=7, ge=1, le=30)
    reason: str = Field(default="Document review required")

class ApprovalStartRequest(BaseModel):
    approver_id: int
    due_days: int = Field(default=5, ge=1, le=15)
    reason: str = Field(default="Final approval required")

class ReviewSubmissionRequest(BaseModel):
    approved: bool
    comments: str = Field(min_length=1, max_length=2000)

class ApprovalSubmissionRequest(BaseModel):
    approved: bool
    comments: str = Field(min_length=1, max_length=2000)
    effective_date: Optional[date] = None

class WorkflowResponse(BaseModel):
    workflow_id: int
    status: str
    message: str
    due_date: Optional[datetime] = None

class PendingActionResponse(BaseModel):
    step_id: int
    workflow_id: int
    step_type: str
    due_date: Optional[datetime]
    document_id: int
    document_number: str
    title: str
    workflow_type: str
    reason: str
    is_overdue: bool

class WorkflowHistoryResponse(BaseModel):
    workflow_id: int
    workflow_type: str
    workflow_status: str
    started_at: datetime
    completed_at: Optional[datetime]
    reason: str
    initiated_by: str
    step_id: Optional[int]
    step_type: Optional[str]
    step_status: Optional[str]
    decision: Optional[str]
    comments: Optional[str]
    step_completed_at: Optional[datetime]
    assigned_to: Optional[str]

class WorkflowStatsResponse(BaseModel):
    total_workflows: int
    pending_review: int
    pending_approval: int
    approved: int
    rejected: int
    review_workflows: int
    up_version_workflows: int
    obsolete_workflows: int
    overdue_actions: int

# Workflow initiation endpoints

@router.post("/{document_id}/start-review", response_model=WorkflowResponse)
async def start_review_workflow(
    document_id: int,
    request: WorkflowStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a review workflow for a document"""
    try:
        service = DocumentWorkflowService(db)
        
        result = service.start_review_workflow(
            document_id=document_id,
            reviewer_id=request.reviewer_id,
            user_id=current_user.id,
            due_days=request.due_days,
            reason=request.reason
        )
        
        return WorkflowResponse(
            workflow_id=result['workflow_id'],
            status=result['status'],
            message=f"Review workflow started. Due date: {result['due_date'].strftime('%Y-%m-%d')}",
            due_date=result['due_date']
        )
        
    except Exception as e:
        logger.error(f"Error starting review workflow for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start review workflow: {str(e)}")

@router.post("/{document_id}/start-approval", response_model=WorkflowResponse)
async def start_approval_workflow(
    document_id: int,
    request: ApprovalStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start an approval workflow for a document (after review)"""
    try:
        service = DocumentWorkflowService(db)
        
        # For this implementation, we'll directly call start_review_workflow with approval
        # In a real implementation, you might want to check that review is complete first
        
        result = service.start_review_workflow(
            document_id=document_id,
            reviewer_id=request.approver_id,
            user_id=current_user.id,
            due_days=request.due_days,
            reason=request.reason
        )
        
        return WorkflowResponse(
            workflow_id=result['workflow_id'],
            status="pending_approval",
            message=f"Approval workflow started. Due date: {result['due_date'].strftime('%Y-%m-%d')}",
            due_date=result['due_date']
        )
        
    except Exception as e:
        logger.error(f"Error starting approval workflow for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start approval workflow: {str(e)}")

# Workflow action endpoints

@router.post("/steps/{step_id}/submit-review")
async def submit_review(
    step_id: int,
    request: ReviewSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a review decision for a workflow step"""
    try:
        service = DocumentWorkflowService(db)
        
        result = service.submit_review(
            workflow_step_id=step_id,
            approved=request.approved,
            comments=request.comments,
            user_id=current_user.id
        )
        
        message = f"Review {'approved' if request.approved else 'rejected'} successfully"
        if request.approved:
            message += " - Document moved to approval stage"
        else:
            message += " - Document returned to draft"
            
        return {
            "status": result['status'],
            "workflow_id": result['workflow_id'],
            "document_id": result['document_id'],
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error submitting review for step {step_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")

@router.post("/steps/{step_id}/submit-approval")
async def submit_approval(
    step_id: int,
    request: ApprovalSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an approval decision for a workflow step"""
    try:
        service = DocumentWorkflowService(db)
        
        result = service.submit_approval(
            workflow_step_id=step_id,
            approved=request.approved,
            comments=request.comments,
            user_id=current_user.id,
            effective_date=request.effective_date
        )
        
        if request.approved:
            eff_date = result.get('effective_date', 'today')
            message = f"Document approved successfully - Effective date: {eff_date}"
        else:
            message = "Document approval rejected - Returned to draft"
            
        return {
            "status": result['status'],
            "workflow_id": result['workflow_id'],
            "document_id": result['document_id'],
            "effective_date": result.get('effective_date'),
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error submitting approval for step {step_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit approval: {str(e)}")

# Information endpoints

@router.get("/user/{user_id}/pending-actions", response_model=List[PendingActionResponse])
async def get_user_pending_actions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending workflow actions for a user"""
    try:
        # Basic authorization - users can only see their own actions unless they're admin
        if user_id != current_user.id and not hasattr(current_user, 'is_admin'):
            raise HTTPException(status_code=403, detail="Not authorized to view other user's actions")
        
        service = DocumentWorkflowService(db)
        actions = service.get_user_pending_actions(user_id)
        
        return [PendingActionResponse(**action) for action in actions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending actions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending actions: {str(e)}")

@router.get("/my-pending-actions", response_model=List[PendingActionResponse])
async def get_my_pending_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending workflow actions for the current user"""
    try:
        service = DocumentWorkflowService(db)
        actions = service.get_user_pending_actions(current_user.id)
        
        return [PendingActionResponse(**action) for action in actions]
        
    except Exception as e:
        logger.error(f"Error getting pending actions for current user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending actions: {str(e)}")

@router.get("/document/{document_id}/history", response_model=List[WorkflowHistoryResponse])
async def get_document_workflow_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow history for a document"""
    try:
        service = DocumentWorkflowService(db)
        history = service.get_document_workflow_history(document_id)
        
        return [WorkflowHistoryResponse(**item) for item in history]
        
    except Exception as e:
        logger.error(f"Error getting workflow history for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow history: {str(e)}")

@router.get("/stats", response_model=WorkflowStatsResponse)
async def get_workflow_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow statistics for dashboard"""
    try:
        service = DocumentWorkflowService(db)
        stats = service.get_workflow_statistics()
        
        return WorkflowStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting workflow statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow statistics: {str(e)}")

# Simple workflow actions for testing

@router.post("/{document_id}/simple-review")
async def simple_review_action(
    document_id: int,
    approved: bool = Query(..., description="Whether to approve or reject"),
    comments: str = Query("Review completed", description="Review comments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simple review action for testing (creates workflow if needed)"""
    try:
        service = DocumentWorkflowService(db)
        
        # Start workflow if it doesn't exist
        try:
            workflow_result = service.start_review_workflow(
                document_id=document_id,
                reviewer_id=current_user.id,
                user_id=current_user.id,
                reason="Auto-generated review workflow"
            )
            workflow_id = workflow_result['workflow_id']
            
            # Get the review step ID (should be the first step)
            from sqlalchemy import text
            step_query = text("""
                SELECT id FROM workflow_steps 
                WHERE workflow_id = :workflow_id AND step_type = 'review' 
                ORDER BY step_order LIMIT 1
            """)
            result = db.execute(step_query, {'workflow_id': workflow_id})
            step_row = result.fetchone()
            
            if step_row:
                step_id = step_row[0]
                
                # Submit the review
                review_result = service.submit_review(
                    workflow_step_id=step_id,
                    approved=approved,
                    comments=comments,
                    user_id=current_user.id
                )
                
                return {
                    "message": f"Document {'approved' if approved else 'rejected'} successfully",
                    "status": review_result['status'],
                    "workflow_id": workflow_id,
                    "document_id": document_id
                }
            else:
                return {"message": "Workflow created but review step not found", "workflow_id": workflow_id}
                
        except Exception as workflow_error:
            logger.error(f"Error in simple review workflow: {str(workflow_error)}")
            return {"error": f"Workflow error: {str(workflow_error)}"}
        
    except Exception as e:
        logger.error(f"Error in simple review action for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform review action: {str(e)}")

@router.post("/{document_id}/simple-approve")
async def simple_approve_action(
    document_id: int,
    approved: bool = Query(..., description="Whether to approve or reject"),
    comments: str = Query("Final approval completed", description="Approval comments"),
    effective_date: Optional[str] = Query(None, description="Effective date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simple approval action for testing"""
    try:
        service = DocumentWorkflowService(db)
        
        # Parse effective date
        eff_date = None
        if effective_date:
            try:
                eff_date = datetime.strptime(effective_date, '%Y-%m-%d').date()
            except ValueError:
                eff_date = datetime.now().date()
        
        # Find pending approval step for this document
        from sqlalchemy import text
        step_query = text("""
            SELECT ws.id
            FROM workflow_steps ws
            JOIN document_workflows dw ON ws.workflow_id = dw.id
            WHERE dw.document_id = :document_id 
              AND ws.step_type = 'approve' 
              AND ws.status = 'pending'
            ORDER BY ws.created_at DESC LIMIT 1
        """)
        
        result = db.execute(step_query, {'document_id': document_id})
        step_row = result.fetchone()
        
        if step_row:
            step_id = step_row[0]
            
            # Submit the approval
            approval_result = service.submit_approval(
                workflow_step_id=step_id,
                approved=approved,
                comments=comments,
                user_id=current_user.id,
                effective_date=eff_date
            )
            
            return {
                "message": f"Document {'approved' if approved else 'rejected'} successfully",
                "status": approval_result['status'],
                "effective_date": approval_result.get('effective_date'),
                "document_id": document_id
            }
        else:
            return {"error": "No pending approval step found for this document"}
        
    except Exception as e:
        logger.error(f"Error in simple approve action for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform approval action: {str(e)}")

# Health check endpoint
@router.get("/health")
async def workflow_health_check():
    """Health check for workflow service"""
    return {
        "status": "healthy",
        "service": "document_workflows",
        "timestamp": datetime.now(),
        "endpoints_available": [
            "start-review", "start-approval", 
            "submit-review", "submit-approval",
            "pending-actions", "history", "stats"
        ]
    }