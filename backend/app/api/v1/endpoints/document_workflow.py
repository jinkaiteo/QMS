"""
Document Workflow API Endpoints
Pharmaceutical document approval and review workflows
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document_workflow import (
    DocumentWorkflowInstance, DocumentWorkflowStep, DocumentSignature,
    DocumentComment, WorkflowStatus, ApprovalAction, SignatureType
)
from app.services.document_workflow_service import DocumentWorkflowService

router = APIRouter()


@router.post("/initiate/{document_id}")
async def initiate_workflow(
    document_id: int,
    template_id: Optional[int] = None,
    custom_reviewers: Optional[List[int]] = None,
    custom_approvers: Optional[List[int]] = None,
    due_days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate a workflow for a document"""
    
    try:
        workflow_service = DocumentWorkflowService(db, current_user)
        
        due_date = datetime.utcnow() + timedelta(days=due_days) if due_days else None
        
        workflow = workflow_service.initiate_workflow(
            document_id=document_id,
            template_id=template_id,
            custom_reviewers=custom_reviewers or [],
            custom_approvers=custom_approvers or [],
            due_date=due_date
        )
        
        return {
            "success": True,
            "workflow_id": workflow.id,
            "status": workflow.status,
            "due_date": workflow.due_date,
            "message": "Workflow initiated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{document_id}")
async def get_workflow_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow status for a document"""
    
    workflow_service = DocumentWorkflowService(db, current_user)
    status = workflow_service.get_workflow_status(document_id)
    
    return status


@router.post("/step/{step_id}/complete")
async def complete_workflow_step(
    step_id: int,
    action: ApprovalAction,
    comments: Optional[str] = None,
    signature_meaning: Optional[str] = None,
    signature_method: str = "password",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete a workflow step with approval action"""
    
    try:
        workflow_service = DocumentWorkflowService(db, current_user)
        
        # Prepare signature data if signature is required
        signature_data = None
        if signature_meaning:
            signature_data = {
                "meaning": signature_meaning,
                "method": signature_method,
                "ip_address": "127.0.0.1",  # Would get from request in real implementation
                "user_agent": "QMS Platform"
            }
        
        success = workflow_service.complete_workflow_step(
            step_id=step_id,
            action=action,
            comments=comments,
            signature_data=signature_data
        )
        
        return {
            "success": success,
            "action": action,
            "message": f"Step completed with action: {action}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/my-tasks")
async def get_my_tasks(
    status: Optional[WorkflowStatus] = None,
    overdue_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow tasks assigned to current user"""
    
    workflow_service = DocumentWorkflowService(db, current_user)
    tasks = workflow_service.get_user_tasks(
        status=status,
        overdue_only=overdue_only
    )
    
    # Format tasks for response
    task_list = []
    for task in tasks[skip:skip+limit]:
        workflow = task.workflow_instance
        document = workflow.document
        
        task_info = {
            "step_id": task.id,
            "workflow_id": workflow.id,
            "document_id": document.id,
            "document_title": document.title,
            "step_name": task.step_name,
            "step_type": task.step_type,
            "status": task.status,
            "due_date": task.due_date,
            "assigned_at": task.assigned_at,
            "priority": workflow.priority,
            "initiated_by": workflow.initiator.username,
            "days_overdue": (datetime.utcnow() - task.due_date).days if task.due_date and task.due_date < datetime.utcnow() else 0
        }
        task_list.append(task_info)
    
    return {
        "tasks": task_list,
        "total": len(tasks),
        "overdue_count": len([t for t in tasks if t.due_date and t.due_date < datetime.utcnow()])
    }


@router.post("/step/{step_id}/delegate")
async def delegate_task(
    step_id: int,
    delegate_to_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delegate a workflow task to another user"""
    
    try:
        workflow_service = DocumentWorkflowService(db, current_user)
        
        success = workflow_service.delegate_task(
            step_id=step_id,
            delegate_to_id=delegate_to_id,
            reason=reason
        )
        
        return {
            "success": success,
            "message": "Task delegated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/comment")
async def add_comment(
    document_id: int,
    comment_text: str,
    comment_type: str = "general",
    workflow_step_id: Optional[int] = None,
    page_number: Optional[int] = None,
    section_reference: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a document during workflow"""
    
    try:
        workflow_service = DocumentWorkflowService(db, current_user)
        
        comment = workflow_service.add_comment(
            document_id=document_id,
            comment_text=comment_text,
            comment_type=comment_type,
            workflow_step_id=workflow_step_id,
            page_number=page_number,
            section_reference=section_reference
        )
        
        return {
            "success": True,
            "comment_id": comment.id,
            "created_at": comment.created_at,
            "message": "Comment added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comment/{document_id}")
async def get_document_comments(
    document_id: int,
    workflow_step_id: Optional[int] = None,
    comment_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comments for a document"""
    
    query = db.query(DocumentComment).filter(
        DocumentComment.document_id == document_id
    )
    
    if workflow_step_id:
        query = query.filter(DocumentComment.workflow_step_id == workflow_step_id)
    
    if comment_type:
        query = query.filter(DocumentComment.comment_type == comment_type)
    
    comments = query.order_by(DocumentComment.created_at.desc()).all()
    
    comment_list = []
    for comment in comments:
        comment_info = {
            "id": comment.id,
            "comment_text": comment.comment_text,
            "comment_type": comment.comment_type,
            "page_number": comment.page_number,
            "section_reference": comment.section_reference,
            "created_by": comment.created_by.username,
            "created_at": comment.created_at,
            "is_resolved": comment.is_resolved,
            "resolved_by": comment.resolved_by.username if comment.resolved_by else None,
            "resolved_at": comment.resolved_at,
            "priority": comment.priority
        }
        comment_list.append(comment_info)
    
    return {
        "comments": comment_list,
        "total": len(comment_list)
    }


@router.get("/signatures/{document_id}")
async def get_document_signatures(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get electronic signatures for a document"""
    
    signatures = db.query(DocumentSignature).filter(
        DocumentSignature.document_id == document_id,
        DocumentSignature.is_valid == True
    ).order_by(DocumentSignature.signed_at.asc()).all()
    
    signature_list = []
    for signature in signatures:
        signature_info = {
            "id": signature.id,
            "signer": signature.signer.username,
            "signature_type": signature.signature_type,
            "signature_meaning": signature.signature_meaning,
            "signed_at": signature.signed_at,
            "signature_method": signature.signature_method,
            "is_valid": signature.is_valid,
            "regulatory_basis": signature.regulatory_basis
        }
        signature_list.append(signature_info)
    
    return {
        "signatures": signature_list,
        "total": len(signature_list)
    }


@router.get("/dashboard")
async def get_workflow_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow dashboard statistics"""
    
    # Get user's active tasks
    workflow_service = DocumentWorkflowService(db, current_user)
    my_tasks = workflow_service.get_user_tasks()
    
    # Get overall workflow statistics
    total_active_workflows = db.query(DocumentWorkflowInstance).filter(
        DocumentWorkflowInstance.status == WorkflowStatus.IN_PROGRESS
    ).count()
    
    overdue_workflows = db.query(DocumentWorkflowInstance).filter(
        DocumentWorkflowInstance.status == WorkflowStatus.IN_PROGRESS,
        DocumentWorkflowInstance.due_date < datetime.utcnow()
    ).count()
    
    completed_this_month = db.query(DocumentWorkflowInstance).filter(
        DocumentWorkflowInstance.status == WorkflowStatus.COMPLETED,
        DocumentWorkflowInstance.completed_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    # Get pending approvals by type
    pending_reviews = len([t for t in my_tasks if t.step_type == "review"])
    pending_approvals = len([t for t in my_tasks if t.step_type == "approval"])
    
    return {
        "my_tasks": {
            "total": len(my_tasks),
            "pending_reviews": pending_reviews,
            "pending_approvals": pending_approvals,
            "overdue": len([t for t in my_tasks if t.due_date and t.due_date < datetime.utcnow()])
        },
        "overall_stats": {
            "active_workflows": total_active_workflows,
            "overdue_workflows": overdue_workflows,
            "completed_this_month": completed_this_month
        }
    }


@router.post("/template")
async def create_workflow_template(
    name: str,
    description: str,
    document_type_id: int,
    review_days: int = 5,
    approval_days: int = 3,
    approval_levels: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a workflow template"""
    
    from app.models.document_workflow import DocumentWorkflowTemplate
    
    template = DocumentWorkflowTemplate(
        name=name,
        description=description,
        document_type_id=document_type_id,
        review_days=review_days,
        approval_days=approval_days,
        approval_levels=approval_levels,
        created_by_id=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {
        "success": True,
        "template_id": template.id,
        "message": "Workflow template created successfully"
    }