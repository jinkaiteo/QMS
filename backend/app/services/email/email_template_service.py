# Email Template Service - Phase B Sprint 2 Day 5
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from enum import Enum
from jinja2 import Template, Environment, BaseLoader

logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """Email template types"""
    COMPLIANCE_ALERT = "compliance_alert"
    REPORT_DELIVERY = "report_delivery" 
    AUDIT_NOTIFICATION = "audit_notification"
    SYSTEM_ALERT = "system_alert"
    TRAINING_REMINDER = "training_reminder"
    QUALITY_EVENT = "quality_event"
    CAPA_UPDATE = "capa_update"
    REGULATORY_SUBMISSION = "regulatory_submission"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"
    GENERAL_NOTIFICATION = "general_notification"

@dataclass
class EmailTemplate:
    """Email template definition"""
    template_id: str
    name: str
    template_type: TemplateType
    subject_template: str
    html_content: str
    text_content: str
    description: str
    variables: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    active: bool = True
    version: str = "1.0"

class EmailTemplateService:
    """
    Email Template Management Service
    Professional email templates for compliance and reporting notifications
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.jinja_env = Environment(loader=BaseLoader())
        
        # Load pre-built templates
        self.templates = self._load_default_templates()
        
    async def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get email template by ID"""
        return next((t for t in self.templates if t.template_id == template_id), None)
    
    async def get_templates_by_type(self, template_type: TemplateType) -> List[EmailTemplate]:
        """Get templates by type"""
        return [t for t in self.templates if t.template_type == template_type]
    
    async def render_template(self, 
                            template_id: str, 
                            variables: Dict[str, Any]) -> Dict[str, str]:
        """Render template with variables"""
        
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        try:
            # Render subject
            subject_template = self.jinja_env.from_string(template.subject_template)
            rendered_subject = subject_template.render(**variables)
            
            # Render HTML content
            html_template = self.jinja_env.from_string(template.html_content)
            rendered_html = html_template.render(**variables)
            
            # Render text content
            text_template = self.jinja_env.from_string(template.text_content)
            rendered_text = text_template.render(**variables)
            
            return {
                'subject': rendered_subject,
                'html_content': rendered_html,
                'text_content': rendered_text
            }
            
        except Exception as e:
            logger.error(f"Template rendering failed for {template_id}: {str(e)}")
            raise e
    
    def _load_default_templates(self) -> List[EmailTemplate]:
        """Load default email templates"""
        
        templates = []
        
        # Compliance Alert Template
        templates.append(EmailTemplate(
            template_id="compliance_alert_critical",
            name="Critical Compliance Alert",
            template_type=TemplateType.COMPLIANCE_ALERT,
            subject_template="🚨 CRITICAL: Compliance Violation Detected - {{ violation_type }}",
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #d32f2f; color: white; padding: 20px; margin: -30px -30px 20px -30px; border-radius: 8px 8px 0 0; }
        .alert-icon { font-size: 24px; margin-right: 10px; }
        .content { line-height: 1.6; color: #333; }
        .details { background-color: #ffebee; padding: 15px; border-left: 4px solid #d32f2f; margin: 20px 0; }
        .action-required { background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="alert-icon">🚨</span>
            <strong>CRITICAL COMPLIANCE VIOLATION</strong>
        </div>
        
        <div class="content">
            <h2>Immediate Attention Required</h2>
            <p>A critical compliance violation has been detected in the QMS platform that requires immediate attention.</p>
            
            <div class="details">
                <h3>Violation Details:</h3>
                <ul>
                    <li><strong>Type:</strong> {{ violation_type }}</li>
                    <li><strong>Module:</strong> {{ module }}</li>
                    <li><strong>Severity:</strong> {{ severity }}</li>
                    <li><strong>Detected:</strong> {{ detected_at }}</li>
                    <li><strong>Rule:</strong> {{ rule_name }}</li>
                </ul>
                
                <p><strong>Description:</strong> {{ description }}</p>
            </div>
            
            <div class="action-required">
                <h3>Immediate Actions Required:</h3>
                <ol>
                    {% for action in required_actions %}
                    <li>{{ action }}</li>
                    {% endfor %}
                </ol>
                
                <p><strong>Deadline:</strong> {{ remediation_deadline }}</p>
            </div>
            
            <p>Please log into the QMS platform immediately to review and address this violation.</p>
            
            <a href="{{ platform_url }}" class="button">Access QMS Platform</a>
        </div>
        
        <div class="footer">
            <p>This is an automated notification from the QMS Compliance Monitoring System.</p>
            <p>If you have questions, contact the Compliance Team at {{ compliance_email }}</p>
        </div>
    </div>
</body>
</html>
            """,
            text_content="""
CRITICAL COMPLIANCE VIOLATION DETECTED

Immediate Attention Required

A critical compliance violation has been detected in the QMS platform.

Violation Details:
- Type: {{ violation_type }}
- Module: {{ module }}
- Severity: {{ severity }}
- Detected: {{ detected_at }}
- Rule: {{ rule_name }}

Description: {{ description }}

Immediate Actions Required:
{% for action in required_actions %}
{{ loop.index }}. {{ action }}
{% endfor %}

Deadline: {{ remediation_deadline }}

Please log into the QMS platform immediately to review and address this violation.

Platform URL: {{ platform_url }}

This is an automated notification from the QMS Compliance Monitoring System.
Contact the Compliance Team at {{ compliance_email }} if you have questions.
            """,
            description="Critical compliance violation alert template",
            variables=["violation_type", "module", "severity", "detected_at", "rule_name", "description", "required_actions", "remediation_deadline", "platform_url", "compliance_email"]
        ))
        
        # Report Delivery Template
        templates.append(EmailTemplate(
            template_id="report_delivery_scheduled",
            name="Scheduled Report Delivery",
            template_type=TemplateType.REPORT_DELIVERY,
            subject_template="📊 {{ report_type }} Report - {{ report_period }}",
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #1976d2; color: white; padding: 20px; margin: -30px -30px 20px -30px; border-radius: 8px 8px 0 0; }
        .content { line-height: 1.6; color: #333; }
        .report-summary { background-color: #e3f2fd; padding: 15px; border-left: 4px solid #1976d2; margin: 20px 0; }
        .metrics { display: flex; justify-content: space-between; margin: 20px 0; }
        .metric { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 4px; flex: 1; margin: 0 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #1976d2; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
        .attachment { background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span>📊</span>
            <strong>{{ report_type }} Report Delivery</strong>
        </div>
        
        <div class="content">
            <h2>{{ report_name }}</h2>
            <p>Your scheduled {{ report_type }} report for {{ report_period }} is ready.</p>
            
            <div class="report-summary">
                <h3>Report Summary:</h3>
                <ul>
                    <li><strong>Generated:</strong> {{ generated_at }}</li>
                    <li><strong>Period:</strong> {{ report_period }}</li>
                    <li><strong>Data Sources:</strong> {{ data_sources_count }}</li>
                    <li><strong>Processing Time:</strong> {{ processing_time }}</li>
                </ul>
            </div>
            
            {% if metrics %}
            <div class="metrics">
                {% for metric in metrics %}
                <div class="metric">
                    <div class="metric-value">{{ metric.value }}</div>
                    <div>{{ metric.label }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <h3>Attached Reports:</h3>
            {% for attachment in attachments %}
            <div class="attachment">
                📎 {{ attachment.filename }} ({{ attachment.size }})
            </div>
            {% endfor %}
            
            {% if platform_url %}
            <p>You can also access this report online:</p>
            <a href="{{ platform_url }}" class="button">View Online</a>
            {% endif %}
            
            {% if next_delivery %}
            <p><strong>Next Delivery:</strong> {{ next_delivery }}</p>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>This report was automatically generated by the QMS Reporting System.</p>
            <p>Questions? Contact {{ support_email }}</p>
        </div>
    </div>
</body>
</html>
            """,
            text_content="""
{{ report_type }} Report Delivery

{{ report_name }}

Your scheduled {{ report_type }} report for {{ report_period }} is ready.

Report Summary:
- Generated: {{ generated_at }}
- Period: {{ report_period }}
- Data Sources: {{ data_sources_count }}
- Processing Time: {{ processing_time }}

{% if metrics %}
Key Metrics:
{% for metric in metrics %}
- {{ metric.label }}: {{ metric.value }}
{% endfor %}
{% endif %}

Attached Reports:
{% for attachment in attachments %}
- {{ attachment.filename }} ({{ attachment.size }})
{% endfor %}

{% if platform_url %}
View online: {{ platform_url }}
{% endif %}

{% if next_delivery %}
Next Delivery: {{ next_delivery }}
{% endif %}

This report was automatically generated by the QMS Reporting System.
Questions? Contact {{ support_email }}
            """,
            description="Scheduled report delivery notification",
            variables=["report_type", "report_name", "report_period", "generated_at", "data_sources_count", "processing_time", "metrics", "attachments", "platform_url", "next_delivery", "support_email"]
        ))
        
        # Training Reminder Template
        templates.append(EmailTemplate(
            template_id="training_reminder_due",
            name="Training Due Reminder",
            template_type=TemplateType.TRAINING_REMINDER,
            subject_template="📚 Training Due: {{ training_program }} - Due {{ due_date }}",
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #2e7d32; color: white; padding: 20px; margin: -30px -30px 20px -30px; border-radius: 8px 8px 0 0; }
        .content { line-height: 1.6; color: #333; }
        .training-info { background-color: #e8f5e8; padding: 15px; border-left: 4px solid #2e7d32; margin: 20px 0; }
        .urgent { background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background-color: #2e7d32; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span>📚</span>
            <strong>Training Reminder</strong>
        </div>
        
        <div class="content">
            <h2>Training Assignment Due</h2>
            <p>Hello {{ employee_name }},</p>
            <p>This is a reminder that you have a training assignment due soon.</p>
            
            <div class="training-info">
                <h3>Training Details:</h3>
                <ul>
                    <li><strong>Program:</strong> {{ training_program }}</li>
                    <li><strong>Due Date:</strong> {{ due_date }}</li>
                    <li><strong>Duration:</strong> {{ estimated_duration }}</li>
                    <li><strong>Type:</strong> {{ training_type }}</li>
                    <li><strong>Assigned:</strong> {{ assigned_date }}</li>
                </ul>
            </div>
            
            {% if days_until_due <= 3 %}
            <div class="urgent">
                <h3>⚠️ Urgent Action Required</h3>
                <p>This training is due in {{ days_until_due }} day(s). Please complete it as soon as possible to maintain compliance.</p>
            </div>
            {% endif %}
            
            <p><strong>Training Description:</strong></p>
            <p>{{ training_description }}</p>
            
            <a href="{{ training_url }}" class="button">Start Training</a>
            
            <p>If you have any questions about this training, please contact your supervisor or the Training Department.</p>
        </div>
        
        <div class="footer">
            <p>This is an automated reminder from the QMS Training Management System.</p>
            <p>Training Department: {{ training_contact }}</p>
        </div>
    </div>
</body>
</html>
            """,
            text_content="""
Training Assignment Due

Hello {{ employee_name }},

This is a reminder that you have a training assignment due soon.

Training Details:
- Program: {{ training_program }}
- Due Date: {{ due_date }}
- Duration: {{ estimated_duration }}
- Type: {{ training_type }}
- Assigned: {{ assigned_date }}

{% if days_until_due <= 3 %}
URGENT ACTION REQUIRED
This training is due in {{ days_until_due }} day(s). Please complete it as soon as possible to maintain compliance.
{% endif %}

Training Description:
{{ training_description }}

Start Training: {{ training_url }}

If you have any questions about this training, please contact your supervisor or the Training Department.

This is an automated reminder from the QMS Training Management System.
Training Department: {{ training_contact }}
            """,
            description="Training assignment due reminder",
            variables=["employee_name", "training_program", "due_date", "estimated_duration", "training_type", "assigned_date", "days_until_due", "training_description", "training_url", "training_contact"]
        ))
        
        # Quality Event Notification Template
        templates.append(EmailTemplate(
            template_id="quality_event_created",
            name="Quality Event Notification",
            template_type=TemplateType.QUALITY_EVENT,
            subject_template="🔍 Quality Event #{{ event_id }}: {{ event_type }} - {{ priority }}",
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #ff5722; color: white; padding: 20px; margin: -30px -30px 20px -30px; border-radius: 8px 8px 0 0; }
        .content { line-height: 1.6; color: #333; }
        .event-details { background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff5722; margin: 20px 0; }
        .priority-high { border-left-color: #d32f2f; background-color: #ffebee; }
        .priority-medium { border-left-color: #ff9800; background-color: #fff8e1; }
        .priority-low { border-left-color: #4caf50; background-color: #e8f5e8; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background-color: #ff5722; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span>🔍</span>
            <strong>Quality Event Notification</strong>
        </div>
        
        <div class="content">
            <h2>Quality Event #{{ event_id }}</h2>
            <p>A new quality event has been {{ action }} in the QMS platform.</p>
            
            <div class="event-details priority-{{ priority|lower }}">
                <h3>Event Details:</h3>
                <ul>
                    <li><strong>Type:</strong> {{ event_type }}</li>
                    <li><strong>Priority:</strong> {{ priority }}</li>
                    <li><strong>Status:</strong> {{ status }}</li>
                    <li><strong>Reporter:</strong> {{ reporter_name }}</li>
                    <li><strong>Department:</strong> {{ department }}</li>
                    <li><strong>Date:</strong> {{ event_date }}</li>
                </ul>
                
                <p><strong>Title:</strong> {{ event_title }}</p>
                <p><strong>Description:</strong> {{ event_description }}</p>
            </div>
            
            {% if assigned_to %}
            <p><strong>Assigned to:</strong> {{ assigned_to }}</p>
            {% endif %}
            
            {% if due_date %}
            <p><strong>Resolution Due:</strong> {{ due_date }}</p>
            {% endif %}
            
            <a href="{{ event_url }}" class="button">View Event Details</a>
            
            <p>Please review this event and take appropriate action as needed.</p>
        </div>
        
        <div class="footer">
            <p>This notification was sent from the QMS Quality Event Management System.</p>
            <p>Quality Department: {{ quality_contact }}</p>
        </div>
    </div>
</body>
</html>
            """,
            text_content="""
Quality Event Notification

Quality Event #{{ event_id }}

A new quality event has been {{ action }} in the QMS platform.

Event Details:
- Type: {{ event_type }}
- Priority: {{ priority }}
- Status: {{ status }}
- Reporter: {{ reporter_name }}
- Department: {{ department }}
- Date: {{ event_date }}

Title: {{ event_title }}
Description: {{ event_description }}

{% if assigned_to %}
Assigned to: {{ assigned_to }}
{% endif %}

{% if due_date %}
Resolution Due: {{ due_date }}
{% endif %}

View Event Details: {{ event_url }}

Please review this event and take appropriate action as needed.

This notification was sent from the QMS Quality Event Management System.
Quality Department: {{ quality_contact }}
            """,
            description="Quality event creation/update notification",
            variables=["event_id", "action", "event_type", "priority", "status", "reporter_name", "department", "event_date", "event_title", "event_description", "assigned_to", "due_date", "event_url", "quality_contact"]
        ))
        
        # Daily Summary Template
        templates.append(EmailTemplate(
            template_id="daily_compliance_summary",
            name="Daily Compliance Summary",
            template_type=TemplateType.DAILY_SUMMARY,
            subject_template="📈 Daily Compliance Summary - {{ summary_date }}",
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #1976d2; color: white; padding: 20px; margin: -30px -30px 20px -30px; border-radius: 8px 8px 0 0; }
        .content { line-height: 1.6; color: #333; }
        .metrics { display: flex; justify-content: space-between; margin: 20px 0; }
        .metric { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 4px; flex: 1; margin: 0 5px; }
        .metric-value { font-size: 20px; font-weight: bold; }
        .score-excellent { color: #4caf50; }
        .score-good { color: #8bc34a; }
        .score-warning { color: #ff9800; }
        .score-critical { color: #f44336; }
        .summary-section { background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span>📈</span>
            <strong>Daily Compliance Summary</strong>
        </div>
        
        <div class="content">
            <h2>Compliance Summary for {{ summary_date }}</h2>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value score-{{ overall_score_class }}">{{ overall_score }}%</div>
                    <div>Overall Score</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ checks_completed }}</div>
                    <div>Checks Completed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ issues_found }}</div>
                    <div>Issues Found</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ auto_resolved }}</div>
                    <div>Auto-Resolved</div>
                </div>
            </div>
            
            <div class="summary-section">
                <h3>Compliance by Module:</h3>
                <ul>
                    {% for module in module_scores %}
                    <li><strong>{{ module.name }}:</strong> {{ module.score }}% ({{ module.status }})</li>
                    {% endfor %}
                </ul>
            </div>
            
            {% if critical_issues %}
            <div class="summary-section">
                <h3>🚨 Critical Issues Requiring Attention:</h3>
                <ul>
                    {% for issue in critical_issues %}
                    <li>{{ issue.description }} ({{ issue.module }})</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if achievements %}
            <div class="summary-section">
                <h3>✅ Today's Achievements:</h3>
                <ul>
                    {% for achievement in achievements %}
                    <li>{{ achievement }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            <p><strong>Tomorrow's Schedule:</strong></p>
            <ul>
                {% for task in tomorrows_tasks %}
                <li>{{ task }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by QMS Compliance Monitoring System on {{ generated_at }}</p>
            <p>View detailed reports: {{ platform_url }}</p>
        </div>
    </div>
</body>
</html>
            """,
            text_content="""
Daily Compliance Summary for {{ summary_date }}

Overall Compliance Score: {{ overall_score }}%
Checks Completed: {{ checks_completed }}
Issues Found: {{ issues_found }}
Auto-Resolved: {{ auto_resolved }}

Compliance by Module:
{% for module in module_scores %}
- {{ module.name }}: {{ module.score }}% ({{ module.status }})
{% endfor %}

{% if critical_issues %}
Critical Issues Requiring Attention:
{% for issue in critical_issues %}
- {{ issue.description }} ({{ issue.module }})
{% endfor %}
{% endif %}

{% if achievements %}
Today's Achievements:
{% for achievement in achievements %}
- {{ achievement }}
{% endfor %}
{% endif %}

Tomorrow's Schedule:
{% for task in tomorrows_tasks %}
- {{ task }}
{% endfor %}

Generated by QMS Compliance Monitoring System on {{ generated_at }}
View detailed reports: {{ platform_url }}
            """,
            description="Daily compliance summary report",
            variables=["summary_date", "overall_score", "overall_score_class", "checks_completed", "issues_found", "auto_resolved", "module_scores", "critical_issues", "achievements", "tomorrows_tasks", "generated_at", "platform_url"]
        ))
        
        return templates

# Factory function
def create_email_template_service(db: Session) -> EmailTemplateService:
    """Create and configure email template service"""
    return EmailTemplateService(db=db)