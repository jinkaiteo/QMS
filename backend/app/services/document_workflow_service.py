"""
Document Workflow Service
Handles document review, approval, and lifecycle workflows
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.logging import get_logger

logger = get_logger(__name__)

class DocumentWorkflowService:
    """Service for managing document workflows and approvals"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def start_review_workflow(
        self, 
        document_id: int, 
        reviewer_id: int, 
        user_id: int,
        due_days: int = 7,
        reason: str = "Initial review"
    ) -> Dict[str, Any]:
        """Start a review workflow for a document"""
        try:
            # Create workflow record
            workflow_query = text("""
                INSERT INTO document_workflows 
                (document_id, workflow_type, status, initiated_by_id, current_step, reason, created_at, updated_at)
                VALUES (:document_id, 'review', 'pending_review', :initiated_by_id, 'review', :reason, NOW(), NOW())
                RETURNING id
            """)
            
            result = self.db.execute(workflow_query, {
                'document_id': document_id,
                'initiated_by_id': user_id,
                'reason': reason
            })
            workflow_id = result.fetchone()[0]
            
            # Create review step
            step_query = text("""
                INSERT INTO workflow_steps 
                (workflow_id, step_type, step_order, assigned_to_id, status, due_date, created_at, updated_at)
                VALUES (:workflow_id, 'review', 1, :assigned_to_id, 'pending', :due_date, NOW(), NOW())
                RETURNING id
            """)
            
            due_date = datetime.now() + timedelta(days=due_days)
            result = self.db.execute(step_query, {
                'workflow_id': workflow_id,
                'assigned_to_id': reviewer_id,
                'due_date': due_date
            })
            review_step_id = result.fetchone()[0]
            
            # Update document status
            doc_query = text("""
                UPDATE documents 
                SET status = 'pending_review', workflow_id = :workflow_id, updated_at = NOW()
                WHERE id = :document_id
            """)
            
            self.db.execute(doc_query, {
                'workflow_id': workflow_id,
                'document_id': document_id
            })
            
            self.db.commit()
            
            logger.info(f"Review workflow started for document {document_id} by user {user_id}")
            
            return {
                'workflow_id': workflow_id,
                'review_step_id': review_step_id,
                'status': 'pending_review',
                'reviewer_id': reviewer_id,
                'due_date': due_date
            }
            
        except Exception as e:
            logger.error(f"Error starting review workflow: {str(e)}")
            self.db.rollback()
            raise
    
    def submit_review(
        self, 
        workflow_step_id: int, 
        approved: bool, 
        comments: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """Submit a review decision"""
        try:
            # Update workflow step
            step_query = text("""
                UPDATE workflow_steps 
                SET status = 'completed', 
                    decision = :decision, 
                    comments = :comments, 
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE id = :step_id
            """)
            
            self.db.execute(step_query, {
                'step_id': workflow_step_id,
                'decision': 'approved' if approved else 'rejected',
                'comments': comments
            })
            
            # Get workflow and document info
            info_query = text("""
                SELECT ws.workflow_id, dw.document_id
                FROM workflow_steps ws
                JOIN document_workflows dw ON ws.workflow_id = dw.id
                WHERE ws.id = :step_id
            """)
            
            result = self.db.execute(info_query, {'step_id': workflow_step_id})
            row = result.fetchone()
            workflow_id, document_id = row[0], row[1]
            
            if approved:
                # Move to approval stage
                workflow_query = text("""
                    UPDATE document_workflows 
                    SET status = 'pending_approval', current_step = 'approval', updated_at = NOW()
                    WHERE id = :workflow_id
                """)
                
                doc_query = text("""
                    UPDATE documents 
                    SET status = 'pending_approval', updated_at = NOW()
                    WHERE id = :document_id
                """)
                
                # Create approval step
                approval_query = text("""
                    INSERT INTO workflow_steps 
                    (workflow_id, step_type, step_order, assigned_to_id, status, due_date, created_at, updated_at)
                    VALUES (:workflow_id, 'approve', 2, :assigned_to_id, 'pending', :due_date, NOW(), NOW())
                """)
                
                self.db.execute(workflow_query, {'workflow_id': workflow_id})
                self.db.execute(doc_query, {'document_id': document_id})
                self.db.execute(approval_query, {
                    'workflow_id': workflow_id,
                    'assigned_to_id': user_id,  # Default to reviewer, should be configurable
                    'due_date': datetime.now() + timedelta(days=5)
                })
                
                status = 'approved_for_approval'
            else:
                # Reject - return to draft
                workflow_query = text("""
                    UPDATE document_workflows 
                    SET status = 'rejected', current_step = 'review', updated_at = NOW()
                    WHERE id = :workflow_id
                """)
                
                doc_query = text("""
                    UPDATE documents 
                    SET status = 'draft', updated_at = NOW()
                    WHERE id = :document_id
                """)
                
                self.db.execute(workflow_query, {'workflow_id': workflow_id})
                self.db.execute(doc_query, {'document_id': document_id})
                
                status = 'rejected'
            
            # Add comment
            comment_query = text("""
                INSERT INTO document_comments 
                (document_id, workflow_step_id, comment_text, comment_type, author_id, created_at, updated_at)
                VALUES (:document_id, :workflow_step_id, :comment_text, 'review', :author_id, NOW(), NOW())
            """)
            
            self.db.execute(comment_query, {
                'document_id': document_id,
                'workflow_step_id': workflow_step_id,
                'comment_text': comments,
                'author_id': user_id
            })
            
            self.db.commit()
            
            logger.info(f"Review submitted for workflow step {workflow_step_id}: {status}")
            
            return {
                'status': status,
                'workflow_id': workflow_id,
                'document_id': document_id,
                'approved': approved,
                'comments': comments
            }
            
        except Exception as e:
            logger.error(f"Error submitting review: {str(e)}")
            self.db.rollback()
            raise
    
    def submit_approval(
        self, 
        workflow_step_id: int, 
        approved: bool, 
        comments: str, 
        user_id: int,
        effective_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Submit a final approval decision"""
        try:
            # Update workflow step
            step_query = text("""
                UPDATE workflow_steps 
                SET status = 'completed', 
                    decision = :decision, 
                    comments = :comments, 
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE id = :step_id
            """)
            
            self.db.execute(step_query, {
                'step_id': workflow_step_id,
                'decision': 'approved' if approved else 'rejected',
                'comments': comments
            })
            
            # Get workflow and document info
            info_query = text("""
                SELECT ws.workflow_id, dw.document_id
                FROM workflow_steps ws
                JOIN document_workflows dw ON ws.workflow_id = dw.id
                WHERE ws.id = :step_id
            """)
            
            result = self.db.execute(info_query, {'step_id': workflow_step_id})
            row = result.fetchone()
            workflow_id, document_id = row[0], row[1]
            
            if approved:
                # Document approved - set effective
                eff_date = effective_date or datetime.now().date()
                
                workflow_query = text("""
                    UPDATE document_workflows 
                    SET status = 'approved', current_step = 'completed', completed_at = NOW(), updated_at = NOW()
                    WHERE id = :workflow_id
                """)
                
                doc_query = text("""
                    UPDATE documents 
                    SET status = 'approved', effective_date = :effective_date, updated_at = NOW()
                    WHERE id = :document_id
                """)
                
                self.db.execute(workflow_query, {'workflow_id': workflow_id})
                self.db.execute(doc_query, {
                    'document_id': document_id,
                    'effective_date': eff_date
                })
                
                status = 'approved'
            else:
                # Reject - return to draft
                workflow_query = text("""
                    UPDATE document_workflows 
                    SET status = 'rejected', current_step = 'approval', updated_at = NOW()
                    WHERE id = :workflow_id
                """)
                
                doc_query = text("""
                    UPDATE documents 
                    SET status = 'draft', updated_at = NOW()
                    WHERE id = :document_id
                """)
                
                self.db.execute(workflow_query, {'workflow_id': workflow_id})
                self.db.execute(doc_query, {'document_id': document_id})
                
                status = 'rejected'
                eff_date = None
            
            # Add comment
            comment_query = text("""
                INSERT INTO document_comments 
                (document_id, workflow_step_id, comment_text, comment_type, author_id, created_at, updated_at)
                VALUES (:document_id, :workflow_step_id, :comment_text, 'approval', :author_id, NOW(), NOW())
            """)
            
            self.db.execute(comment_query, {
                'document_id': document_id,
                'workflow_step_id': workflow_step_id,
                'comment_text': comments,
                'author_id': user_id
            })
            
            self.db.commit()
            
            logger.info(f"Approval submitted for workflow step {workflow_step_id}: {status}")
            
            return {
                'status': status,
                'workflow_id': workflow_id,
                'document_id': document_id,
                'approved': approved,
                'effective_date': eff_date,
                'comments': comments
            }
            
        except Exception as e:
            logger.error(f"Error submitting approval: {str(e)}")
            self.db.rollback()
            raise
    
    def get_user_pending_actions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get pending workflow actions for a user"""
        try:
            query = text("""
                SELECT 
                    ws.id as step_id,
                    ws.workflow_id,
                    ws.step_type,
                    ws.due_date,
                    d.id as document_id,
                    d.document_number,
                    d.title,
                    dw.workflow_type,
                    dw.reason
                FROM workflow_steps ws
                JOIN document_workflows dw ON ws.workflow_id = dw.id
                JOIN documents d ON dw.document_id = d.id
                WHERE ws.assigned_to_id = :user_id
                  AND ws.status = 'pending'
                  AND d.is_deleted = FALSE
                  AND dw.is_deleted = FALSE
                  AND ws.is_deleted = FALSE
                ORDER BY ws.due_date ASC
            """)
            
            result = self.db.execute(query, {'user_id': user_id})
            actions = []
            
            for row in result.fetchall():
                actions.append({
                    'step_id': row.step_id,
                    'workflow_id': row.workflow_id,
                    'step_type': row.step_type,
                    'due_date': row.due_date,
                    'document_id': row.document_id,
                    'document_number': row.document_number,
                    'title': row.title,
                    'workflow_type': row.workflow_type,
                    'reason': row.reason,
                    'is_overdue': row.due_date < datetime.now() if row.due_date else False
                })
            
            return actions
            
        except Exception as e:
            logger.error(f"Error getting pending actions for user {user_id}: {str(e)}")
            return []
    
    def get_document_workflow_history(self, document_id: int) -> List[Dict[str, Any]]:
        """Get workflow history for a document"""
        try:
            query = text("""
                SELECT 
                    dw.id as workflow_id,
                    dw.workflow_type,
                    dw.status as workflow_status,
                    dw.created_at as started_at,
                    dw.completed_at,
                    dw.reason,
                    u1.username as initiated_by,
                    ws.id as step_id,
                    ws.step_type,
                    ws.status as step_status,
                    ws.decision,
                    ws.comments,
                    ws.completed_at as step_completed_at,
                    u2.username as assigned_to
                FROM document_workflows dw
                JOIN users u1 ON dw.initiated_by_id = u1.id
                LEFT JOIN workflow_steps ws ON dw.id = ws.workflow_id
                LEFT JOIN users u2 ON ws.assigned_to_id = u2.id
                WHERE dw.document_id = :document_id
                  AND dw.is_deleted = FALSE
                ORDER BY dw.created_at DESC, ws.step_order ASC
            """)
            
            result = self.db.execute(query, {'document_id': document_id})
            history = []
            
            for row in result.fetchall():
                history.append({
                    'workflow_id': row.workflow_id,
                    'workflow_type': row.workflow_type,
                    'workflow_status': row.workflow_status,
                    'started_at': row.started_at,
                    'completed_at': row.completed_at,
                    'reason': row.reason,
                    'initiated_by': row.initiated_by,
                    'step_id': row.step_id,
                    'step_type': row.step_type,
                    'step_status': row.step_status,
                    'decision': row.decision,
                    'comments': row.comments,
                    'step_completed_at': row.step_completed_at,
                    'assigned_to': row.assigned_to
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting workflow history for document {document_id}: {str(e)}")
            return []
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics for dashboard"""
        try:
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_workflows,
                    COUNT(CASE WHEN status = 'pending_review' THEN 1 END) as pending_review,
                    COUNT(CASE WHEN status = 'pending_approval' THEN 1 END) as pending_approval,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                    COUNT(CASE WHEN workflow_type = 'review' THEN 1 END) as review_workflows,
                    COUNT(CASE WHEN workflow_type = 'up_version' THEN 1 END) as up_version_workflows,
                    COUNT(CASE WHEN workflow_type = 'obsolete' THEN 1 END) as obsolete_workflows
                FROM document_workflows
                WHERE is_deleted = FALSE
            """)
            
            result = self.db.execute(stats_query)
            row = result.fetchone()
            
            overdue_query = text("""
                SELECT COUNT(*) as overdue_actions
                FROM workflow_steps ws
                JOIN document_workflows dw ON ws.workflow_id = dw.id
                WHERE ws.status = 'pending'
                  AND ws.due_date < NOW()
                  AND ws.is_deleted = FALSE
                  AND dw.is_deleted = FALSE
            """)
            
            overdue_result = self.db.execute(overdue_query)
            overdue_count = overdue_result.fetchone()[0]
            
            return {
                'total_workflows': row.total_workflows,
                'pending_review': row.pending_review,
                'pending_approval': row.pending_approval,
                'approved': row.approved,
                'rejected': row.rejected,
                'review_workflows': row.review_workflows,
                'up_version_workflows': row.up_version_workflows,
                'obsolete_workflows': row.obsolete_workflows,
                'overdue_actions': overdue_count
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow statistics: {str(e)}")
            return {}