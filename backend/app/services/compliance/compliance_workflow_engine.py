# Compliance Workflow Engine - Phase B Sprint 2 Day 4
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import json
import logging
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class WorkflowTrigger(Enum):
    """Workflow trigger types"""
    SCHEDULE = "schedule"
    EVENT = "event"
    THRESHOLD = "threshold"
    MANUAL = "manual"
    DEPENDENCY = "dependency"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class ActionType(Enum):
    """Types of workflow actions"""
    COMPLIANCE_CHECK = "compliance_check"
    GENERATE_REPORT = "generate_report"
    SEND_NOTIFICATION = "send_notification"
    UPDATE_RECORD = "update_record"
    CREATE_TASK = "create_task"
    ESCALATE_ISSUE = "escalate_issue"
    AUTO_REMEDIATE = "auto_remediate"
    SCHEDULE_AUDIT = "schedule_audit"

@dataclass
class WorkflowAction:
    """Individual workflow action"""
    action_id: str
    action_type: ActionType
    name: str
    description: str
    parameters: Dict[str, Any]
    timeout_seconds: int = 300
    retry_count: int = 3
    required: bool = True
    condition: Optional[str] = None  # Condition for execution
    dependencies: List[str] = field(default_factory=list)

@dataclass
class WorkflowDefinition:
    """Compliance workflow definition"""
    workflow_id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    trigger_config: Dict[str, Any]
    actions: List[WorkflowAction]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"

@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    action_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    progress_percentage: float = 0.0

@dataclass
class ComplianceWorkflowResult:
    """Result of compliance workflow execution"""
    execution_id: str
    workflow_name: str
    success: bool
    actions_completed: int
    actions_failed: int
    execution_time_ms: int
    compliance_score_impact: float
    notifications_sent: int
    reports_generated: List[str]
    issues_remediated: int
    tasks_created: int

class ComplianceWorkflowEngine:
    """
    Compliance Workflow Automation Engine
    Event-driven compliance automation, monitoring, and remediation workflows
    """
    
    def __init__(self, 
                 db: Session,
                 automated_compliance_service=None,
                 template_library=None,
                 data_integrity_service=None,
                 notification_service=None):
        self.db = db
        self.automated_compliance_service = automated_compliance_service
        self.template_library = template_library
        self.data_integrity_service = data_integrity_service
        self.notification_service = notification_service
        
        # Active workflow executions
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Workflow definitions
        self.workflow_definitions = self._load_workflow_definitions()
        
        # Action registry
        self.action_handlers = self._register_action_handlers()
        
        # Scheduler for time-based workflows
        self.scheduled_workflows: List[Dict[str, Any]] = []
        
    def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a new compliance workflow"""
        
        try:
            # Validate workflow
            validation_result = self._validate_workflow(workflow)
            if not validation_result['valid']:
                logger.error(f"Workflow validation failed: {validation_result['errors']}")
                return False
            
            # Add to definitions
            existing_index = next((i for i, w in enumerate(self.workflow_definitions) 
                                 if w.workflow_id == workflow.workflow_id), None)
            
            if existing_index is not None:
                self.workflow_definitions[existing_index] = workflow
                logger.info(f"Updated workflow: {workflow.name}")
            else:
                self.workflow_definitions.append(workflow)
                logger.info(f"Registered new workflow: {workflow.name}")
            
            # Store in database
            self._store_workflow_definition(workflow)
            
            # Schedule if time-based
            if workflow.trigger == WorkflowTrigger.SCHEDULE:
                self._schedule_workflow(workflow)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.workflow_id}: {str(e)}")
            return False
    
    async def trigger_workflow(self, 
                             workflow_id: str,
                             trigger_data: Dict[str, Any] = None) -> ComplianceWorkflowResult:
        """Trigger workflow execution"""
        
        workflow = self._get_workflow_definition(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if not workflow.enabled:
            raise ValueError(f"Workflow {workflow_id} is disabled")
        
        execution_id = str(uuid.uuid4())
        logger.info(f"Triggering workflow {workflow.name} (execution: {execution_id})")
        
        # Create execution instance
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            started_at=datetime.now(),
            trigger_data=trigger_data or {}
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            # Execute workflow
            result = await self._execute_workflow(workflow, execution)
            
            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            # Store execution results
            await self._store_execution_results(execution, result)
            
            logger.info(f"Workflow {workflow.name} completed successfully")
            
            return result
            
        except Exception as e:
            # Mark as failed
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            logger.error(f"Workflow {workflow.name} failed: {str(e)}")
            
            raise e
        
        finally:
            # Remove from active executions
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def trigger_event_workflows(self, 
                                    event_type: str,
                                    event_data: Dict[str, Any]) -> List[ComplianceWorkflowResult]:
        """Trigger workflows based on system events"""
        
        # Find workflows triggered by this event
        triggered_workflows = []
        for workflow in self.workflow_definitions:
            if (workflow.enabled and 
                workflow.trigger == WorkflowTrigger.EVENT and
                workflow.trigger_config.get('event_type') == event_type):
                triggered_workflows.append(workflow)
        
        if not triggered_workflows:
            logger.debug(f"No workflows triggered for event: {event_type}")
            return []
        
        logger.info(f"Triggering {len(triggered_workflows)} workflows for event: {event_type}")
        
        # Execute triggered workflows concurrently
        tasks = []
        for workflow in triggered_workflows:
            task = self.trigger_workflow(workflow.workflow_id, event_data)
            tasks.append(task)
        
        # Wait for all workflows to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Event workflow failed: {str(result)}")
            else:
                successful_results.append(result)
        
        return successful_results
    
    async def _execute_workflow(self, 
                               workflow: WorkflowDefinition,
                               execution: WorkflowExecution) -> ComplianceWorkflowResult:
        """Execute workflow actions"""
        
        start_time = datetime.now()
        execution.status = WorkflowStatus.RUNNING
        
        actions_completed = 0
        actions_failed = 0
        notifications_sent = 0
        reports_generated = []
        issues_remediated = 0
        tasks_created = 0
        compliance_score_impact = 0.0
        
        # Execute actions in sequence (respecting dependencies)
        for i, action in enumerate(workflow.actions):
            try:
                # Check dependencies
                if not self._check_action_dependencies(action, execution.action_results):
                    logger.warning(f"Skipping action {action.name} due to unmet dependencies")
                    continue
                
                # Check condition
                if action.condition and not self._evaluate_condition(action.condition, execution.trigger_data):
                    logger.info(f"Skipping action {action.name} due to condition not met")
                    continue
                
                # Update progress
                execution.progress_percentage = (i / len(workflow.actions)) * 100
                
                # Execute action
                action_result = await self._execute_action(action, execution)
                execution.action_results[action.action_id] = action_result
                
                # Track metrics
                if action_result.get('success', False):
                    actions_completed += 1
                    
                    # Update specific metrics based on action type
                    if action.action_type == ActionType.SEND_NOTIFICATION:
                        notifications_sent += action_result.get('notifications_sent', 0)
                    elif action.action_type == ActionType.GENERATE_REPORT:
                        reports_generated.extend(action_result.get('reports', []))
                    elif action.action_type == ActionType.AUTO_REMEDIATE:
                        issues_remediated += action_result.get('issues_remediated', 0)
                    elif action.action_type == ActionType.CREATE_TASK:
                        tasks_created += action_result.get('tasks_created', 0)
                    elif action.action_type == ActionType.COMPLIANCE_CHECK:
                        compliance_score_impact += action_result.get('score_impact', 0)
                else:
                    actions_failed += 1
                    if action.required:
                        raise Exception(f"Required action {action.name} failed: {action_result.get('error', 'Unknown error')}")
            
            except Exception as e:
                actions_failed += 1
                logger.error(f"Action {action.name} failed: {str(e)}")
                
                if action.required:
                    raise e
        
        # Calculate execution time
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        execution.progress_percentage = 100.0
        
        return ComplianceWorkflowResult(
            execution_id=execution.execution_id,
            workflow_name=workflow.name,
            success=actions_failed == 0,
            actions_completed=actions_completed,
            actions_failed=actions_failed,
            execution_time_ms=execution_time,
            compliance_score_impact=compliance_score_impact,
            notifications_sent=notifications_sent,
            reports_generated=reports_generated,
            issues_remediated=issues_remediated,
            tasks_created=tasks_created
        )
    
    async def _execute_action(self, 
                            action: WorkflowAction,
                            execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute individual workflow action"""
        
        handler = self.action_handlers.get(action.action_type)
        if not handler:
            raise ValueError(f"No handler for action type: {action.action_type}")
        
        logger.debug(f"Executing action: {action.name}")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                handler(action, execution),
                timeout=action.timeout_seconds
            )
            
            result['success'] = True
            result['action_id'] = action.action_id
            result['executed_at'] = datetime.now().isoformat()
            
            return result
            
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': f"Action timed out after {action.timeout_seconds} seconds",
                'action_id': action.action_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action_id': action.action_id
            }
    
    def _register_action_handlers(self) -> Dict[ActionType, Callable]:
        """Register action handlers"""
        
        return {
            ActionType.COMPLIANCE_CHECK: self._handle_compliance_check,
            ActionType.GENERATE_REPORT: self._handle_generate_report,
            ActionType.SEND_NOTIFICATION: self._handle_send_notification,
            ActionType.UPDATE_RECORD: self._handle_update_record,
            ActionType.CREATE_TASK: self._handle_create_task,
            ActionType.ESCALATE_ISSUE: self._handle_escalate_issue,
            ActionType.AUTO_REMEDIATE: self._handle_auto_remediate,
            ActionType.SCHEDULE_AUDIT: self._handle_schedule_audit
        }
    
    async def _handle_compliance_check(self, 
                                     action: WorkflowAction,
                                     execution: WorkflowExecution) -> Dict[str, Any]:
        """Handle compliance check action"""
        
        if not self.automated_compliance_service:
            return {'error': 'Automated compliance service not available'}
        
        check_type = action.parameters.get('check_type', 'scheduled')
        rule_ids = action.parameters.get('rule_ids')
        
        from .automated_compliance_service import ComplianceCheckType
        
        # Map string to enum
        check_type_map = {
            'real_time': ComplianceCheckType.REAL_TIME,
            'scheduled': ComplianceCheckType.SCHEDULED,
            'event_driven': ComplianceCheckType.EVENT_DRIVEN,
            'on_demand': ComplianceCheckType.ON_DEMAND
        }
        
        check_type_enum = check_type_map.get(check_type, ComplianceCheckType.SCHEDULED)
        
        # Run compliance check
        results = await self.automated_compliance_service.run_automated_compliance_check(
            check_type=check_type_enum,
            rule_ids=rule_ids
        )
        
        # Calculate impact
        total_score = sum(result.score for result in results.values())
        avg_score = total_score / len(results) if results else 0
        
        return {
            'check_results': {rule_id: {'score': result.score, 'status': result.status.value} 
                            for rule_id, result in results.items()},
            'average_score': avg_score,
            'score_impact': avg_score - 80,  # Assuming 80 is baseline
            'rules_checked': len(results),
            'violations_found': sum(len(result.violations) for result in results.values())
        }
    
    async def _handle_generate_report(self, 
                                    action: WorkflowAction,
                                    execution: WorkflowExecution) -> Dict[str, Any]:
        """Handle report generation action"""
        
        if not self.template_library:
            return {'error': 'Template library not available'}
        
        template_id = action.parameters.get('template_id')
        parameters = action.parameters.get('parameters', {})
        
        if not template_id:
            return {'error': 'Template ID not specified'}
        
        # Merge execution trigger data with parameters
        final_parameters = {**parameters, **execution.trigger_data}
        
        # Generate report
        result = await self.template_library.generate_regulatory_report(
            template_id=template_id,
            parameters=final_parameters
        )
        
        return {
            'reports': result.output_files,
            'compliance_score': result.compliance_score,
            'generation_time_ms': result.generation_time_ms,
            'validation_passed': result.validation_passed
        }
    
    async def _handle_send_notification(self, 
                                      action: WorkflowAction,
                                      execution: WorkflowExecution) -> Dict[str, Any]:
        """Handle notification sending action"""
        
        recipients = action.parameters.get('recipients', [])
        subject = action.parameters.get('subject', 'Compliance Notification')
        message = action.parameters.get('message', '')
        
        # Replace placeholders in message
        formatted_message = self._format_message(message, execution.trigger_data)
        
        # Send notifications (simulated)
        notifications_sent = 0
        for recipient in recipients:
            try:
                # Here would be actual notification sending logic
                logger.info(f"Sending notification to {recipient}: {subject}")
                notifications_sent += 1
            except Exception as e:
                logger.error(f"Failed to send notification to {recipient}: {str(e)}")
        
        return {
            'notifications_sent': notifications_sent,
            'recipients': recipients,
            'subject': subject
        }
    
    def _load_workflow_definitions(self) -> List[WorkflowDefinition]:
        """Load pre-defined compliance workflows"""
        
        workflows = []
        
        # Daily Compliance Check Workflow
        workflows.append(WorkflowDefinition(
            workflow_id="daily_compliance_check",
            name="Daily Compliance Monitoring",
            description="Automated daily compliance checking and reporting",
            trigger=WorkflowTrigger.SCHEDULE,
            trigger_config={"schedule": "0 6 * * *"},  # Daily at 6 AM
            actions=[
                WorkflowAction(
                    action_id="run_compliance_checks",
                    action_type=ActionType.COMPLIANCE_CHECK,
                    name="Run Compliance Checks",
                    description="Execute all scheduled compliance checks",
                    parameters={
                        "check_type": "scheduled",
                        "rule_ids": None  # All rules
                    }
                ),
                WorkflowAction(
                    action_id="generate_daily_report",
                    action_type=ActionType.GENERATE_REPORT,
                    name="Generate Daily Compliance Report",
                    description="Generate daily compliance summary report",
                    parameters={
                        "template_id": "daily_compliance_summary",
                        "parameters": {
                            "start_date": "yesterday",
                            "end_date": "today"
                        }
                    },
                    dependencies=["run_compliance_checks"]
                ),
                WorkflowAction(
                    action_id="notify_compliance_team",
                    action_type=ActionType.SEND_NOTIFICATION,
                    name="Notify Compliance Team",
                    description="Send daily compliance report to team",
                    parameters={
                        "recipients": ["compliance@company.com"],
                        "subject": "Daily Compliance Report - {date}",
                        "message": "Daily compliance check completed. Overall score: {compliance_score}%"
                    },
                    dependencies=["generate_daily_report"]
                )
            ]
        ))
        
        # Critical Issue Response Workflow
        workflows.append(WorkflowDefinition(
            workflow_id="critical_issue_response",
            name="Critical Compliance Issue Response",
            description="Immediate response to critical compliance issues",
            trigger=WorkflowTrigger.EVENT,
            trigger_config={"event_type": "critical_compliance_violation"},
            actions=[
                WorkflowAction(
                    action_id="immediate_assessment",
                    action_type=ActionType.COMPLIANCE_CHECK,
                    name="Immediate Compliance Assessment",
                    description="Run focused compliance check on affected area",
                    parameters={
                        "check_type": "on_demand",
                        "rule_ids": ["affected_rule_id"]
                    }
                ),
                WorkflowAction(
                    action_id="auto_remediate",
                    action_type=ActionType.AUTO_REMEDIATE,
                    name="Auto-Remediate Issues",
                    description="Attempt automatic remediation of issues",
                    parameters={
                        "auto_remediation_enabled": True,
                        "backup_before_action": True
                    },
                    dependencies=["immediate_assessment"]
                ),
                WorkflowAction(
                    action_id="escalate_critical",
                    action_type=ActionType.ESCALATE_ISSUE,
                    name="Escalate Critical Issue",
                    description="Escalate to management if auto-remediation fails",
                    parameters={
                        "escalation_level": "management",
                        "urgency": "immediate"
                    },
                    condition="auto_remediation_failed",
                    dependencies=["auto_remediate"]
                ),
                WorkflowAction(
                    action_id="emergency_notification",
                    action_type=ActionType.SEND_NOTIFICATION,
                    name="Emergency Notification",
                    description="Send immediate notification to stakeholders",
                    parameters={
                        "recipients": ["compliance@company.com", "management@company.com"],
                        "subject": "CRITICAL: Compliance Violation Detected",
                        "message": "Critical compliance violation detected: {violation_details}"
                    }
                )
            ]
        ))
        
        # Weekly Audit Preparation Workflow
        workflows.append(WorkflowDefinition(
            workflow_id="weekly_audit_prep",
            name="Weekly Audit Preparation",
            description="Weekly audit preparation and compliance review",
            trigger=WorkflowTrigger.SCHEDULE,
            trigger_config={"schedule": "0 9 * * 1"},  # Monday at 9 AM
            actions=[
                WorkflowAction(
                    action_id="comprehensive_compliance_check",
                    action_type=ActionType.COMPLIANCE_CHECK,
                    name="Comprehensive Compliance Review",
                    description="Run full compliance assessment",
                    parameters={
                        "check_type": "scheduled",
                        "rule_ids": None
                    }
                ),
                WorkflowAction(
                    action_id="generate_audit_report",
                    action_type=ActionType.GENERATE_REPORT,
                    name="Generate Audit Readiness Report",
                    description="Generate comprehensive audit readiness report",
                    parameters={
                        "template_id": "audit_readiness_report",
                        "parameters": {
                            "start_date": "last_week",
                            "end_date": "today"
                        }
                    },
                    dependencies=["comprehensive_compliance_check"]
                ),
                WorkflowAction(
                    action_id="schedule_remediation_tasks",
                    action_type=ActionType.CREATE_TASK,
                    name="Schedule Remediation Tasks",
                    description="Create tasks for identified compliance gaps",
                    parameters={
                        "task_type": "compliance_remediation",
                        "priority": "high"
                    },
                    dependencies=["comprehensive_compliance_check"]
                )
            ]
        ))
        
        return workflows
    
    def _get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID"""
        return next((w for w in self.workflow_definitions if w.workflow_id == workflow_id), None)

# Factory function
def create_compliance_workflow_engine(db: Session, **services) -> ComplianceWorkflowEngine:
    """Create and configure compliance workflow engine"""
    return ComplianceWorkflowEngine(db=db, **services)