# Notification Service - Phase B Sprint 2 Day 5
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    COMPLIANCE_ALERT = "compliance_alert"
    COMPLIANCE_SUMMARY = "compliance_summary"
    REPORT_READY = "report_ready"
    TRAINING_DUE = "training_due"
    QUALITY_EVENT = "quality_event"
    CAPA_UPDATE = "capa_update"
    AUDIT_REMINDER = "audit_reminder"
    SYSTEM_ALERT = "system_alert"
    DEADLINE_WARNING = "deadline_warning"
    APPROVAL_REQUEST = "approval_request"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    SLACK = "slack"
    TEAMS = "teams"

@dataclass
class NotificationRule:
    """Notification rule configuration"""
    rule_id: str
    name: str
    notification_type: NotificationType
    trigger_conditions: Dict[str, Any]
    recipients: List[str]
    channels: List[NotificationChannel]
    template_id: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    enabled: bool = True
    cooldown_minutes: int = 60  # Minimum time between notifications
    escalation_rules: Optional[Dict[str, Any]] = None

@dataclass
class Notification:
    """Individual notification"""
    notification_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    recipients: List[str]
    channels: List[NotificationChannel]
    subject: str
    content: str
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)
    scheduled_time: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivery_status: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class NotificationService:
    """
    Comprehensive Notification Service
    Multi-channel notifications with intelligent routing and escalation
    """
    
    def __init__(self, 
                 db: Session,
                 email_service=None,
                 email_template_service=None):
        self.db = db
        self.email_service = email_service
        self.email_template_service = email_template_service
        
        # Notification rules
        self.notification_rules = self._load_notification_rules()
        
        # Channel handlers
        self.channel_handlers = self._setup_channel_handlers()
        
        # Tracking
        self.sent_notifications: Dict[str, datetime] = {}
        
    async def send_notification(self, notification: Notification) -> Dict[str, Any]:
        """Send notification through specified channels"""
        
        logger.info(f"Sending notification: {notification.notification_type.value} to {len(notification.recipients)} recipients")
        
        delivery_results = {}
        
        # Send through each channel
        for channel in notification.channels:
            try:
                handler = self.channel_handlers.get(channel)
                if handler:
                    result = await handler(notification)
                    delivery_results[channel.value] = result
                else:
                    delivery_results[channel.value] = {
                        'success': False,
                        'error': f'No handler for channel: {channel.value}'
                    }
            except Exception as e:
                delivery_results[channel.value] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Failed to send notification via {channel.value}: {str(e)}")
        
        # Update notification status
        notification.sent_at = datetime.now()
        notification.delivery_status = delivery_results
        
        # Store notification record
        await self._store_notification(notification)
        
        # Calculate overall success
        successful_channels = len([r for r in delivery_results.values() if r.get('success', False)])
        total_channels = len(notification.channels)
        
        return {
            'notification_id': notification.notification_id,
            'success': successful_channels > 0,
            'channels_attempted': total_channels,
            'channels_successful': successful_channels,
            'delivery_results': delivery_results
        }
    
    async def send_compliance_alert(self, 
                                  alert_data: Dict[str, Any],
                                  priority: NotificationPriority = NotificationPriority.HIGH) -> Dict[str, Any]:
        """Send compliance violation alert"""
        
        # Determine recipients based on severity
        recipients = self._get_compliance_alert_recipients(alert_data, priority)
        
        # Create notification
        notification = Notification(
            notification_id=f"compliance_alert_{int(datetime.now().timestamp())}",
            notification_type=NotificationType.COMPLIANCE_ALERT,
            priority=priority,
            recipients=recipients,
            channels=[NotificationChannel.EMAIL],
            subject=f"🚨 Compliance Alert: {alert_data.get('violation_type', 'Unknown')}",
            content="Compliance violation detected - see template for details",
            template_id="compliance_alert_critical",
            template_variables=alert_data,
            metadata={'alert_source': 'compliance_automation'}
        )
        
        return await self.send_notification(notification)
    
    async def send_report_delivery_notification(self, 
                                              report_data: Dict[str, Any],
                                              recipients: List[str]) -> Dict[str, Any]:
        """Send report delivery notification"""
        
        notification = Notification(
            notification_id=f"report_delivery_{int(datetime.now().timestamp())}",
            notification_type=NotificationType.REPORT_READY,
            priority=NotificationPriority.NORMAL,
            recipients=recipients,
            channels=[NotificationChannel.EMAIL],
            subject=f"📊 Report Ready: {report_data.get('report_name', 'QMS Report')}",
            content="Your scheduled report is ready",
            template_id="report_delivery_scheduled",
            template_variables=report_data,
            metadata={'report_source': 'scheduled_delivery'}
        )
        
        return await self.send_notification(notification)
    
    async def send_training_reminder(self, 
                                   training_data: Dict[str, Any],
                                   employee_email: str) -> Dict[str, Any]:
        """Send training due reminder"""
        
        # Determine urgency based on due date
        due_date = training_data.get('due_date')
        priority = NotificationPriority.NORMAL
        
        if due_date:
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            
            days_until_due = (due_date - datetime.now()).days
            if days_until_due <= 1:
                priority = NotificationPriority.URGENT
            elif days_until_due <= 3:
                priority = NotificationPriority.HIGH
        
        notification = Notification(
            notification_id=f"training_reminder_{int(datetime.now().timestamp())}",
            notification_type=NotificationType.TRAINING_DUE,
            priority=priority,
            recipients=[employee_email],
            channels=[NotificationChannel.EMAIL],
            subject=f"📚 Training Due: {training_data.get('training_program', 'Training Assignment')}",
            content="Training assignment due soon",
            template_id="training_reminder_due",
            template_variables=training_data,
            metadata={'training_source': 'training_management'}
        )
        
        return await self.send_notification(notification)
    
    async def send_quality_event_notification(self, 
                                            event_data: Dict[str, Any],
                                            notification_type: str = "created") -> Dict[str, Any]:
        """Send quality event notification"""
        
        # Determine recipients based on event priority and type
        recipients = self._get_quality_event_recipients(event_data)
        
        # Determine priority
        event_priority = event_data.get('priority', 'medium').lower()
        notification_priority = NotificationPriority.NORMAL
        
        if event_priority == 'high':
            notification_priority = NotificationPriority.HIGH
        elif event_priority == 'critical':
            notification_priority = NotificationPriority.URGENT
        
        # Add action to template variables
        event_data_with_action = {**event_data, 'action': notification_type}
        
        notification = Notification(
            notification_id=f"quality_event_{notification_type}_{int(datetime.now().timestamp())}",
            notification_type=NotificationType.QUALITY_EVENT,
            priority=notification_priority,
            recipients=recipients,
            channels=[NotificationChannel.EMAIL],
            subject=f"🔍 Quality Event: {event_data.get('event_title', 'Quality Event')}",
            content=f"Quality event {notification_type}",
            template_id="quality_event_created",
            template_variables=event_data_with_action,
            metadata={'event_source': 'quality_management'}
        )
        
        return await self.send_notification(notification)
    
    async def send_daily_compliance_summary(self, 
                                          summary_data: Dict[str, Any],
                                          recipients: List[str]) -> Dict[str, Any]:
        """Send daily compliance summary"""
        
        notification = Notification(
            notification_id=f"daily_summary_{int(datetime.now().timestamp())}",
            notification_type=NotificationType.COMPLIANCE_SUMMARY,
            priority=NotificationPriority.NORMAL,
            recipients=recipients,
            channels=[NotificationChannel.EMAIL],
            subject=f"📈 Daily Compliance Summary - {summary_data.get('summary_date', 'Today')}",
            content="Daily compliance summary report",
            template_id="daily_compliance_summary",
            template_variables=summary_data,
            metadata={'summary_source': 'compliance_automation'}
        )
        
        return await self.send_notification(notification)
    
    async def process_notification_rules(self, 
                                       trigger_event: str,
                                       event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process notification rules for a trigger event"""
        
        results = []
        
        for rule in self.notification_rules:
            if not rule.enabled:
                continue
            
            # Check if rule matches trigger event
            if self._rule_matches_event(rule, trigger_event, event_data):
                # Check cooldown
                if self._is_rule_in_cooldown(rule):
                    continue
                
                # Create and send notification
                notification = self._create_notification_from_rule(rule, event_data)
                result = await self.send_notification(notification)
                results.append(result)
                
                # Update cooldown tracking
                self.sent_notifications[rule.rule_id] = datetime.now()
        
        return results
    
    def _setup_channel_handlers(self) -> Dict[NotificationChannel, callable]:
        """Setup notification channel handlers"""
        
        return {
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.IN_APP: self._send_in_app_notification,
            NotificationChannel.SMS: self._send_sms_notification,
            NotificationChannel.SLACK: self._send_slack_notification,
            NotificationChannel.TEAMS: self._send_teams_notification
        }
    
    async def _send_email_notification(self, notification: Notification) -> Dict[str, Any]:
        """Send notification via email"""
        
        if not self.email_service:
            return {'success': False, 'error': 'Email service not available'}
        
        from .email_service import EmailMessage, EmailRecipient
        
        # Process template if specified
        content = notification.content
        subject = notification.subject
        
        if notification.template_id and self.email_template_service:
            try:
                rendered = await self.email_template_service.render_template(
                    notification.template_id,
                    notification.template_variables
                )
                content = rendered.get('html_content', notification.content)
                subject = rendered.get('subject', notification.subject)
            except Exception as e:
                logger.warning(f"Template rendering failed: {str(e)}")
        
        # Create email message
        email_message = EmailMessage(
            message_id=f"notification_{notification.notification_id}",
            subject=subject,
            sender_email="notifications@qms-company.com",
            sender_name="QMS Notification System",
            recipients=[EmailRecipient(email=email, name=email) for email in notification.recipients],
            html_content=content,
            priority=self._convert_to_email_priority(notification.priority)
        )
        
        # Send email
        result = await self.email_service.send_email(email_message)
        
        return {
            'success': result.status.value == 'sent',
            'message_id': email_message.message_id,
            'delivery_result': result.status.value,
            'error': result.error_message
        }
    
    async def _send_in_app_notification(self, notification: Notification) -> Dict[str, Any]:
        """Send in-app notification"""
        
        # Store in-app notification in database
        try:
            for recipient in notification.recipients:
                await self._store_in_app_notification(notification, recipient)
            
            return {
                'success': True,
                'recipients_notified': len(notification.recipients)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _send_sms_notification(self, notification: Notification) -> Dict[str, Any]:
        """Send SMS notification (placeholder)"""
        
        # SMS integration would be implemented here
        logger.info(f"SMS notification sent to {len(notification.recipients)} recipients (simulated)")
        
        return {
            'success': True,
            'provider': 'simulated',
            'recipients_notified': len(notification.recipients)
        }
    
    async def _send_slack_notification(self, notification: Notification) -> Dict[str, Any]:
        """Send Slack notification (placeholder)"""
        
        # Slack integration would be implemented here
        logger.info(f"Slack notification sent to {len(notification.recipients)} recipients (simulated)")
        
        return {
            'success': True,
            'provider': 'simulated',
            'recipients_notified': len(notification.recipients)
        }
    
    async def _send_teams_notification(self, notification: Notification) -> Dict[str, Any]:
        """Send Microsoft Teams notification (placeholder)"""
        
        # Teams integration would be implemented here
        logger.info(f"Teams notification sent to {len(notification.recipients)} recipients (simulated)")
        
        return {
            'success': True,
            'provider': 'simulated',
            'recipients_notified': len(notification.recipients)
        }
    
    def _get_compliance_alert_recipients(self, alert_data: Dict[str, Any], priority: NotificationPriority) -> List[str]:
        """Get recipients for compliance alerts based on severity"""
        
        recipients = ["compliance@company.com"]
        
        if priority in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]:
            recipients.extend([
                "compliance.manager@company.com",
                "quality.director@company.com"
            ])
        
        # Add module-specific recipients
        module = alert_data.get('module', '')
        if module == 'edms':
            recipients.append("document.control@company.com")
        elif module == 'qrm':
            recipients.append("quality.manager@company.com")
        elif module == 'training':
            recipients.append("training.manager@company.com")
        elif module == 'lims':
            recipients.append("lab.manager@company.com")
        
        return list(set(recipients))  # Remove duplicates
    
    def _get_quality_event_recipients(self, event_data: Dict[str, Any]) -> List[str]:
        """Get recipients for quality event notifications"""
        
        recipients = ["quality@company.com"]
        
        # Add assigned person if specified
        if event_data.get('assigned_to'):
            recipients.append(event_data['assigned_to'])
        
        # Add department-specific recipients
        department = event_data.get('department', '')
        if department:
            recipients.append(f"{department.lower()}@company.com")
        
        return list(set(recipients))
    
    def _convert_to_email_priority(self, priority: NotificationPriority):
        """Convert notification priority to email priority"""
        
        from .email_service import EmailPriority
        
        mapping = {
            NotificationPriority.LOW: EmailPriority.LOW,
            NotificationPriority.NORMAL: EmailPriority.NORMAL,
            NotificationPriority.HIGH: EmailPriority.HIGH,
            NotificationPriority.URGENT: EmailPriority.URGENT,
            NotificationPriority.CRITICAL: EmailPriority.URGENT
        }
        
        return mapping.get(priority, EmailPriority.NORMAL)
    
    def _load_notification_rules(self) -> List[NotificationRule]:
        """Load notification rules configuration"""
        
        # This would typically load from database
        # For now, return some default rules
        
        return [
            NotificationRule(
                rule_id="critical_compliance_violation",
                name="Critical Compliance Violation Alert",
                notification_type=NotificationType.COMPLIANCE_ALERT,
                trigger_conditions={
                    "compliance_score": {"operator": "lt", "value": 75},
                    "severity": {"operator": "eq", "value": "critical"}
                },
                recipients=["compliance@company.com", "management@company.com"],
                channels=[NotificationChannel.EMAIL],
                template_id="compliance_alert_critical",
                priority=NotificationPriority.CRITICAL,
                cooldown_minutes=30
            ),
            NotificationRule(
                rule_id="training_overdue",
                name="Training Overdue Alert",
                notification_type=NotificationType.TRAINING_DUE,
                trigger_conditions={
                    "days_overdue": {"operator": "gt", "value": 0}
                },
                recipients=["training@company.com"],
                channels=[NotificationChannel.EMAIL],
                template_id="training_reminder_due",
                priority=NotificationPriority.HIGH,
                cooldown_minutes=1440  # 24 hours
            )
        ]

# Factory function
def create_notification_service(db: Session, **services) -> NotificationService:
    """Create and configure notification service"""
    return NotificationService(db=db, **services)