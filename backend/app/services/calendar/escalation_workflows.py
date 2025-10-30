# Multi-level Escalation Workflows - Phase B Sprint 2 Day 6
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class EscalationTrigger(Enum):
    """Escalation trigger types"""
    TIME_BASED = "time_based"
    CONDITION_BASED = "condition_based"
    MANUAL = "manual"
    SYSTEM_EVENT = "system_event"
    APPROVAL_TIMEOUT = "approval_timeout"
    COMPLIANCE_VIOLATION = "compliance_violation"

class EscalationLevel(Enum):
    """Escalation authority levels"""
    PEER = "peer"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    BOARD = "board"
    EXTERNAL = "external"

class ApprovalAction(Enum):
    """Approval actions"""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    DEFER = "defer"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class EscalationStep:
    """Individual escalation step"""
    step_id: str
    step_number: int
    level: EscalationLevel
    approvers: List[str]
    timeout_hours: int
    required_approvals: int = 1
    allow_delegation: bool = True
    auto_approve_conditions: Optional[Dict[str, Any]] = None
    escalation_message_template: Optional[str] = None

@dataclass
class ApprovalRequest:
    """Approval request details"""
    request_id: str
    workflow_id: str
    step_id: str
    requester: str
    approvers: List[str]
    subject: str
    description: str
    priority: str
    context_data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    approved_by: List[str] = field(default_factory=list)
    rejected_by: List[str] = field(default_factory=list)
    status: str = "pending"

@dataclass
class EscalationWorkflow:
    """Complete escalation workflow definition"""
    workflow_id: str
    name: str
    description: str
    trigger: EscalationTrigger
    trigger_conditions: Dict[str, Any]
    steps: List[EscalationStep]
    auto_start: bool = True
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0

@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    initiated_by: str
    current_step: int
    status: WorkflowStatus
    context_data: Dict[str, Any]
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    approval_requests: List[ApprovalRequest] = field(default_factory=list)
    escalation_history: List[Dict[str, Any]] = field(default_factory=list)

class EscalationWorkflowService:
    """
    Multi-level Escalation Workflow Service
    Advanced approval chains and escalation management
    """
    
    def __init__(self, 
                 db: Session,
                 notification_service=None,
                 conditional_logic_engine=None):
        self.db = db
        self.notification_service = notification_service
        self.conditional_logic_engine = conditional_logic_engine
        
        # Workflow registry
        self.workflows = self._load_escalation_workflows()
        
        # Active executions
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Organization hierarchy
        self.org_hierarchy = self._load_organization_hierarchy()
        
    async def start_escalation_workflow(self, 
                                      workflow_id: str,
                                      initiated_by: str,
                                      context_data: Dict[str, Any]) -> WorkflowExecution:
        """Start an escalation workflow"""
        
        workflow = self._get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if not workflow.enabled:
            raise ValueError(f"Workflow {workflow_id} is disabled")
        
        execution_id = str(uuid.uuid4())
        logger.info(f"Starting escalation workflow: {workflow.name} (execution: {execution_id})")
        
        # Create execution instance
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            initiated_by=initiated_by,
            current_step=0,
            status=WorkflowStatus.IN_PROGRESS,
            context_data=context_data
        )
        
        # Add to active executions
        self.active_executions[execution_id] = execution
        
        # Start first step
        await self._execute_workflow_step(execution, workflow)
        
        # Update workflow statistics
        workflow.last_used = datetime.now()
        workflow.usage_count += 1
        
        # Store execution
        await self._store_workflow_execution(execution)
        
        return execution
    
    async def process_approval_response(self, 
                                      request_id: str,
                                      approver: str,
                                      action: ApprovalAction,
                                      comment: Optional[str] = None) -> Dict[str, Any]:
        """Process approval response"""
        
        # Find approval request
        execution, request = await self._find_approval_request(request_id)
        if not execution or not request:
            raise ValueError(f"Approval request {request_id} not found")
        
        workflow = self._get_workflow(execution.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {execution.workflow_id} not found")
        
        logger.info(f"Processing approval response: {action.value} from {approver}")
        
        # Validate approver
        if approver not in request.approvers:
            raise ValueError(f"User {approver} is not authorized to approve this request")
        
        # Process action
        if action == ApprovalAction.APPROVE:
            if approver not in request.approved_by:
                request.approved_by.append(approver)
        elif action == ApprovalAction.REJECT:
            if approver not in request.rejected_by:
                request.rejected_by.append(approver)
        elif action == ApprovalAction.DELEGATE:
            # Handle delegation logic
            await self._handle_delegation(request, approver, comment)
        elif action == ApprovalAction.ESCALATE:
            # Force escalation to next level
            await self._force_escalation(execution, workflow, comment)
        
        # Check if step requirements are met
        step = workflow.steps[execution.current_step]
        step_result = await self._evaluate_step_completion(request, step)
        
        # Update execution based on step result
        if step_result['completed']:
            if step_result['approved']:
                # Move to next step or complete workflow
                await self._advance_workflow(execution, workflow)
            else:
                # Workflow rejected
                execution.status = WorkflowStatus.REJECTED
                execution.completed_at = datetime.now()
        
        # Store updates
        await self._store_workflow_execution(execution)
        
        # Send notifications
        await self._send_approval_notifications(execution, request, action, approver, comment)
        
        return {
            'request_id': request_id,
            'action': action.value,
            'approver': approver,
            'status': execution.status.value,
            'current_step': execution.current_step,
            'step_completed': step_result.get('completed', False),
            'workflow_completed': execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.REJECTED]
        }
    
    async def check_escalation_timeouts(self) -> List[Dict[str, Any]]:
        """Check for escalation timeouts and trigger automatic escalations"""
        
        timeout_actions = []
        current_time = datetime.now()
        
        for execution in list(self.active_executions.values()):
            if execution.status != WorkflowStatus.WAITING_APPROVAL:
                continue
            
            # Check for expired approval requests
            for request in execution.approval_requests:
                if (request.expires_at and 
                    request.expires_at <= current_time and 
                    request.status == "pending"):
                    
                    workflow = self._get_workflow(execution.workflow_id)
                    if workflow:
                        timeout_action = await self._handle_approval_timeout(execution, workflow, request)
                        timeout_actions.append(timeout_action)
        
        return timeout_actions
    
    async def _execute_workflow_step(self, execution: WorkflowExecution, workflow: EscalationWorkflow):
        """Execute current workflow step"""
        
        if execution.current_step >= len(workflow.steps):
            # Workflow completed
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            return
        
        step = workflow.steps[execution.current_step]
        logger.info(f"Executing workflow step {execution.current_step + 1}: {step.level.value}")
        
        # Check auto-approve conditions
        if step.auto_approve_conditions and self.conditional_logic_engine:
            should_auto_approve = await self._check_auto_approve_conditions(
                step.auto_approve_conditions, 
                execution.context_data
            )
            
            if should_auto_approve:
                logger.info(f"Auto-approving step {execution.current_step + 1}")
                await self._advance_workflow(execution, workflow)
                return
        
        # Create approval request
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            workflow_id=execution.workflow_id,
            step_id=step.step_id,
            requester=execution.initiated_by,
            approvers=step.approvers,
            subject=f"Approval Required: {workflow.name}",
            description=f"Step {execution.current_step + 1} - {step.level.value} approval required",
            priority=execution.context_data.get('priority', 'normal'),
            context_data=execution.context_data,
            expires_at=datetime.now() + timedelta(hours=step.timeout_hours)
        )
        
        # Add to execution
        execution.approval_requests.append(request)
        execution.status = WorkflowStatus.WAITING_APPROVAL
        
        # Send approval notifications
        await self._send_approval_request_notifications(execution, request, step)
    
    async def _advance_workflow(self, execution: WorkflowExecution, workflow: EscalationWorkflow):
        """Advance workflow to next step"""
        
        execution.current_step += 1
        
        if execution.current_step >= len(workflow.steps):
            # Workflow completed successfully
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            logger.info(f"Workflow completed: {execution.execution_id}")
            
            # Send completion notification
            await self._send_workflow_completion_notification(execution, workflow)
        else:
            # Continue to next step
            execution.status = WorkflowStatus.IN_PROGRESS
            await self._execute_workflow_step(execution, workflow)
    
    async def _handle_approval_timeout(self, 
                                     execution: WorkflowExecution,
                                     workflow: EscalationWorkflow,
                                     request: ApprovalRequest) -> Dict[str, Any]:
        """Handle approval timeout"""
        
        logger.warning(f"Approval timeout for request {request.request_id}")
        
        # Mark request as expired
        request.status = "expired"
        
        # Add to escalation history
        escalation_entry = {
            'timestamp': datetime.now().isoformat(),
            'reason': 'approval_timeout',
            'step': execution.current_step,
            'approvers': request.approvers,
            'timeout_hours': workflow.steps[execution.current_step].timeout_hours
        }
        execution.escalation_history.append(escalation_entry)
        
        # Escalate to next level
        if execution.current_step < len(workflow.steps) - 1:
            execution.current_step += 1
            await self._execute_workflow_step(execution, workflow)
            
            action = {
                'type': 'escalated',
                'reason': 'timeout',
                'new_step': execution.current_step,
                'execution_id': execution.execution_id
            }
        else:
            # No more escalation levels, mark as expired
            execution.status = WorkflowStatus.EXPIRED
            execution.completed_at = datetime.now()
            
            action = {
                'type': 'expired',
                'reason': 'final_timeout',
                'execution_id': execution.execution_id
            }
        
        # Send timeout notification
        await self._send_timeout_notification(execution, workflow, request)
        
        return action
    
    async def _evaluate_step_completion(self, 
                                      request: ApprovalRequest,
                                      step: EscalationStep) -> Dict[str, Any]:
        """Evaluate if workflow step is completed"""
        
        approvals_received = len(request.approved_by)
        rejections_received = len(request.rejected_by)
        
        # Check if required approvals met
        approval_threshold_met = approvals_received >= step.required_approvals
        
        # Check if any rejections (assuming one rejection fails the step)
        has_rejections = rejections_received > 0
        
        if has_rejections:
            return {
                'completed': True,
                'approved': False,
                'reason': 'rejected',
                'approvals': approvals_received,
                'rejections': rejections_received
            }
        elif approval_threshold_met:
            return {
                'completed': True,
                'approved': True,
                'reason': 'approved',
                'approvals': approvals_received,
                'rejections': rejections_received
            }
        else:
            return {
                'completed': False,
                'approved': False,
                'reason': 'pending',
                'approvals': approvals_received,
                'rejections': rejections_received,
                'required': step.required_approvals
            }
    
    async def _send_approval_request_notifications(self, 
                                                 execution: WorkflowExecution,
                                                 request: ApprovalRequest,
                                                 step: EscalationStep):
        """Send approval request notifications"""
        
        if not self.notification_service:
            return
        
        # Prepare notification data
        notification_data = {
            'execution_id': execution.execution_id,
            'request_id': request.request_id,
            'workflow_name': self._get_workflow(execution.workflow_id).name,
            'step_level': step.level.value,
            'step_number': execution.current_step + 1,
            'requester': execution.initiated_by,
            'subject': request.subject,
            'description': request.description,
            'priority': request.priority,
            'expires_at': request.expires_at.isoformat() if request.expires_at else None,
            'approval_url': f"/approvals/{request.request_id}",
            'context_summary': self._generate_context_summary(execution.context_data)
        }
        
        # Send to each approver
        for approver in request.approvers:
            await self.notification_service.send_notification({
                'notification_type': 'approval_request',
                'priority': 'high' if request.priority == 'urgent' else 'normal',
                'recipients': [approver],
                'subject': f"Approval Required: {request.subject}",
                'template_id': 'approval_request',
                'template_variables': notification_data,
                'channels': ['email', 'in_app']
            })
    
    def _load_escalation_workflows(self) -> List[EscalationWorkflow]:
        """Load escalation workflow definitions"""
        
        workflows = []
        
        # Critical Compliance Violation Workflow
        workflows.append(EscalationWorkflow(
            workflow_id="critical_compliance_escalation",
            name="Critical Compliance Violation Escalation",
            description="Escalation workflow for critical compliance violations",
            trigger=EscalationTrigger.COMPLIANCE_VIOLATION,
            trigger_conditions={
                "compliance_score": {"operator": "lt", "value": 75},
                "severity": {"operator": "eq", "value": "critical"}
            },
            steps=[
                EscalationStep(
                    step_id="compliance_manager_review",
                    step_number=1,
                    level=EscalationLevel.SUPERVISOR,
                    approvers=["compliance.manager@company.com"],
                    timeout_hours=2,
                    required_approvals=1,
                    escalation_message_template="critical_compliance_escalation"
                ),
                EscalationStep(
                    step_id="quality_director_approval",
                    step_number=2,
                    level=EscalationLevel.DIRECTOR,
                    approvers=["quality.director@company.com"],
                    timeout_hours=4,
                    required_approvals=1,
                    escalation_message_template="director_escalation"
                ),
                EscalationStep(
                    step_id="executive_approval",
                    step_number=3,
                    level=EscalationLevel.EXECUTIVE,
                    approvers=["ceo@company.com", "coo@company.com"],
                    timeout_hours=8,
                    required_approvals=1,
                    escalation_message_template="executive_escalation"
                )
            ],
            auto_start=True
        ))
        
        # High-Priority Report Delivery Workflow
        workflows.append(EscalationWorkflow(
            workflow_id="priority_report_approval",
            name="High-Priority Report Delivery Approval",
            description="Approval workflow for high-priority regulatory reports",
            trigger=EscalationTrigger.CONDITION_BASED,
            trigger_conditions={
                "report_type": {"operator": "in", "value": ["fda_submission", "regulatory_audit"]},
                "priority": {"operator": "eq", "value": "high"}
            },
            steps=[
                EscalationStep(
                    step_id="department_manager_approval",
                    step_number=1,
                    level=EscalationLevel.MANAGER,
                    approvers=["department.manager@company.com"],
                    timeout_hours=6,
                    required_approvals=1
                ),
                EscalationStep(
                    step_id="regulatory_director_approval",
                    step_number=2,
                    level=EscalationLevel.DIRECTOR,
                    approvers=["regulatory.director@company.com"],
                    timeout_hours=12,
                    required_approvals=1
                )
            ],
            auto_start=False
        ))
        
        return workflows
    
    def _load_organization_hierarchy(self) -> Dict[str, Any]:
        """Load organization hierarchy for escalation"""
        
        return {
            'departments': {
                'quality': {
                    'manager': 'quality.manager@company.com',
                    'director': 'quality.director@company.com'
                },
                'compliance': {
                    'manager': 'compliance.manager@company.com',
                    'director': 'compliance.director@company.com'
                },
                'regulatory': {
                    'manager': 'regulatory.manager@company.com',
                    'director': 'regulatory.director@company.com'
                }
            },
            'executive': ['ceo@company.com', 'coo@company.com', 'cfo@company.com']
        }
    
    def _get_workflow(self, workflow_id: str) -> Optional[EscalationWorkflow]:
        """Get workflow by ID"""
        return next((w for w in self.workflows if w.workflow_id == workflow_id), None)

# Factory function
def create_escalation_workflow_service(db: Session, **services) -> EscalationWorkflowService:
    """Create and configure escalation workflow service"""
    return EscalationWorkflowService(db=db, **services)