# Delivery Scheduler Service - Phase B Sprint 2 Day 5
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import json
import logging
from enum import Enum
import croniter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

class DeliveryFrequency(Enum):
    """Delivery frequency options"""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM_CRON = "custom_cron"

class DeliveryCondition(Enum):
    """Conditions for delivery"""
    ALWAYS = "always"
    COMPLIANCE_THRESHOLD = "compliance_threshold"
    ISSUE_COUNT_THRESHOLD = "issue_count_threshold"
    DATA_AVAILABLE = "data_available"
    BUSINESS_DAYS_ONLY = "business_days_only"
    CUSTOM_CONDITION = "custom_condition"

@dataclass
class DeliverySchedule:
    """Scheduled delivery configuration"""
    schedule_id: str
    name: str
    description: str
    frequency: DeliveryFrequency
    cron_expression: Optional[str] = None
    template_id: Optional[str] = None
    report_template_id: Optional[str] = None
    recipients: List[str] = field(default_factory=list)
    conditions: List[DeliveryCondition] = field(default_factory=list)
    condition_parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_delivery: Optional[datetime] = None
    next_delivery: Optional[datetime] = None
    delivery_count: int = 0

@dataclass
class ScheduledDelivery:
    """Individual scheduled delivery execution"""
    delivery_id: str
    schedule_id: str
    scheduled_time: datetime
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, failed, skipped
    recipients: List[str] = field(default_factory=list)
    generated_reports: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None

class DeliveryScheduler:
    """
    Comprehensive Delivery Scheduler
    CRON-based scheduling with business rules and conditional delivery
    """
    
    def __init__(self, 
                 db: Session,
                 email_service=None,
                 template_processing_service=None,
                 regulatory_template_library=None,
                 compliance_service=None):
        self.db = db
        self.email_service = email_service
        self.template_processing_service = template_processing_service
        self.regulatory_template_library = regulatory_template_library
        self.compliance_service = compliance_service
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        
        # Active schedules
        self.delivery_schedules: List[DeliverySchedule] = []
        
        # Business day configuration
        self.business_days = [0, 1, 2, 3, 4]  # Monday-Friday
        self.holidays = []  # Will be loaded from configuration
        
    async def start_scheduler(self):
        """Start the delivery scheduler"""
        
        logger.info("Starting delivery scheduler")
        
        # Load existing schedules
        await self._load_delivery_schedules()
        
        # Start the scheduler
        self.scheduler.start()
        
        # Schedule all active deliveries
        await self._schedule_all_deliveries()
        
        logger.info(f"Delivery scheduler started with {len(self.delivery_schedules)} schedules")
    
    async def stop_scheduler(self):
        """Stop the delivery scheduler"""
        
        logger.info("Stopping delivery scheduler")
        self.scheduler.shutdown()
    
    async def create_delivery_schedule(self, schedule: DeliverySchedule) -> bool:
        """Create a new delivery schedule"""
        
        try:
            # Validate schedule
            validation_result = self._validate_schedule(schedule)
            if not validation_result['valid']:
                logger.error(f"Schedule validation failed: {validation_result['errors']}")
                return False
            
            # Calculate next delivery time
            schedule.next_delivery = self._calculate_next_delivery(schedule)
            
            # Add to active schedules
            self.delivery_schedules.append(schedule)
            
            # Store in database
            await self._store_delivery_schedule(schedule)
            
            # Schedule in job scheduler
            await self._schedule_delivery(schedule)
            
            logger.info(f"Created delivery schedule: {schedule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create delivery schedule: {str(e)}")
            return False
    
    async def update_delivery_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing delivery schedule"""
        
        try:
            # Find schedule
            schedule = next((s for s in self.delivery_schedules if s.schedule_id == schedule_id), None)
            if not schedule:
                logger.error(f"Schedule not found: {schedule_id}")
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(schedule, field):
                    setattr(schedule, field, value)
            
            # Recalculate next delivery
            schedule.next_delivery = self._calculate_next_delivery(schedule)
            
            # Update in database
            await self._store_delivery_schedule(schedule)
            
            # Reschedule
            self.scheduler.remove_job(f"delivery_{schedule_id}")
            await self._schedule_delivery(schedule)
            
            logger.info(f"Updated delivery schedule: {schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update delivery schedule: {str(e)}")
            return False
    
    async def execute_scheduled_delivery(self, schedule_id: str, manual: bool = False) -> ScheduledDelivery:
        """Execute a scheduled delivery"""
        
        start_time = datetime.now()
        delivery_id = f"delivery_{schedule_id}_{int(start_time.timestamp())}"
        
        logger.info(f"Executing scheduled delivery: {schedule_id} ({'manual' if manual else 'automatic'})")
        
        # Find schedule
        schedule = next((s for s in self.delivery_schedules if s.schedule_id == schedule_id), None)
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")
        
        # Create delivery record
        delivery = ScheduledDelivery(
            delivery_id=delivery_id,
            schedule_id=schedule_id,
            scheduled_time=start_time,
            recipients=schedule.recipients.copy(),
            status="executing"
        )
        
        try:
            # Check delivery conditions
            if not manual and not await self._check_delivery_conditions(schedule):
                delivery.status = "skipped"
                delivery.executed_at = datetime.now()
                logger.info(f"Delivery skipped due to conditions: {schedule_id}")
                return delivery
            
            # Generate reports if template specified
            generated_reports = []
            if schedule.report_template_id:
                reports = await self._generate_scheduled_reports(schedule)
                generated_reports.extend(reports)
                delivery.generated_reports = generated_reports
            
            # Send notifications
            if schedule.template_id and self.email_service:
                await self._send_scheduled_notifications(schedule, delivery, generated_reports)
            
            # Update delivery status
            delivery.status = "completed"
            delivery.executed_at = datetime.now()
            delivery.execution_time_ms = int((delivery.executed_at - start_time).total_seconds() * 1000)
            
            # Update schedule statistics
            schedule.last_delivery = delivery.executed_at
            schedule.delivery_count += 1
            schedule.next_delivery = self._calculate_next_delivery(schedule)
            
            # Store delivery record
            await self._store_delivery_record(delivery)
            await self._store_delivery_schedule(schedule)
            
            logger.info(f"Scheduled delivery completed: {delivery_id}")
            
        except Exception as e:
            delivery.status = "failed"
            delivery.error_message = str(e)
            delivery.executed_at = datetime.now()
            
            logger.error(f"Scheduled delivery failed: {delivery_id} - {str(e)}")
            
            # Store failure record
            await self._store_delivery_record(delivery)
        
        return delivery
    
    async def _generate_scheduled_reports(self, schedule: DeliverySchedule) -> List[str]:
        """Generate reports for scheduled delivery"""
        
        generated_reports = []
        
        try:
            if schedule.report_template_id and self.regulatory_template_library:
                # Generate regulatory report
                parameters = {
                    'start_date': (datetime.now() - timedelta(days=7)).isoformat(),
                    'end_date': datetime.now().isoformat(),
                    **schedule.condition_parameters
                }
                
                result = await self.regulatory_template_library.generate_regulatory_report(
                    template_id=schedule.report_template_id,
                    parameters=parameters
                )
                
                generated_reports.extend(result.output_files)
                
            elif schedule.report_template_id and self.template_processing_service:
                # Generate template processing report
                from ..reporting.template_processing_service import TemplateProcessingRequest
                
                processing_request = TemplateProcessingRequest(
                    template_id=int(schedule.report_template_id),
                    parameters=schedule.condition_parameters,
                    output_format='both',
                    validate_template=True,
                    generate_charts=True,
                    cache_results=False
                )
                
                result = await self.template_processing_service.process_template(processing_request)
                
                if result.success:
                    generated_reports.extend(result.generated_files)
            
        except Exception as e:
            logger.error(f"Report generation failed for schedule {schedule.schedule_id}: {str(e)}")
        
        return generated_reports
    
    async def _send_scheduled_notifications(self, 
                                          schedule: DeliverySchedule,
                                          delivery: ScheduledDelivery,
                                          generated_reports: List[str]):
        """Send scheduled notification emails"""
        
        if not self.email_service or not schedule.template_id:
            return
        
        from .email_service import EmailMessage, EmailRecipient, EmailAttachment
        import os
        
        # Prepare template variables
        template_variables = {
            'schedule_name': schedule.name,
            'delivery_date': delivery.scheduled_time.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'reports_count': len(generated_reports),
            'delivery_id': delivery.delivery_id,
            **schedule.condition_parameters
        }
        
        # Create attachments from generated reports
        attachments = []
        for report_path in generated_reports:
            if os.path.exists(report_path):
                with open(report_path, 'rb') as f:
                    content = f.read()
                
                filename = os.path.basename(report_path)
                content_type = 'application/pdf' if filename.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                
                attachments.append(EmailAttachment(
                    filename=filename,
                    content=content,
                    content_type=content_type
                ))
        
        # Create email message
        message = EmailMessage(
            message_id=f"scheduled_{delivery.delivery_id}",
            subject=f"Scheduled Delivery: {schedule.name}",
            sender_email="qms-reports@company.com",
            sender_name="QMS Reporting System",
            recipients=[EmailRecipient(email=email, name=email) for email in schedule.recipients],
            template_id=schedule.template_id,
            template_variables=template_variables,
            attachments=attachments
        )
        
        # Send email
        await self.email_service.send_email(message)
    
    async def _check_delivery_conditions(self, schedule: DeliverySchedule) -> bool:
        """Check if delivery conditions are met"""
        
        for condition in schedule.conditions:
            if condition == DeliveryCondition.ALWAYS:
                continue
                
            elif condition == DeliveryCondition.BUSINESS_DAYS_ONLY:
                if datetime.now().weekday() not in self.business_days:
                    return False
                if datetime.now().date() in self.holidays:
                    return False
                    
            elif condition == DeliveryCondition.COMPLIANCE_THRESHOLD:
                if self.compliance_service:
                    threshold = schedule.condition_parameters.get('compliance_threshold', 85)
                    score = await self.compliance_service.get_real_time_compliance_score()
                    if score.overall_score < threshold:
                        return False
                        
            elif condition == DeliveryCondition.ISSUE_COUNT_THRESHOLD:
                threshold = schedule.condition_parameters.get('max_issues', 5)
                # Would check current issue count
                # For now, assume condition is met
                pass
                
            elif condition == DeliveryCondition.DATA_AVAILABLE:
                # Check if required data is available
                # Would implement specific data availability checks
                pass
                
            elif condition == DeliveryCondition.CUSTOM_CONDITION:
                # Custom condition evaluation
                condition_func = schedule.condition_parameters.get('condition_function')
                if condition_func and not await self._evaluate_custom_condition(condition_func, schedule):
                    return False
        
        return True
    
    def _calculate_next_delivery(self, schedule: DeliverySchedule) -> datetime:
        """Calculate next delivery time based on schedule"""
        
        now = datetime.now()
        
        if schedule.frequency == DeliveryFrequency.IMMEDIATE:
            return now
            
        elif schedule.frequency == DeliveryFrequency.HOURLY:
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
        elif schedule.frequency == DeliveryFrequency.DAILY:
            # Default to 8 AM next day
            next_day = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
            return next_day
            
        elif schedule.frequency == DeliveryFrequency.WEEKLY:
            # Default to Monday 8 AM
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_monday = (now + timedelta(days=days_ahead)).replace(hour=8, minute=0, second=0, microsecond=0)
            return next_monday
            
        elif schedule.frequency == DeliveryFrequency.MONTHLY:
            # First Monday of next month at 8 AM
            next_month = now.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1, hour=8, minute=0, second=0, microsecond=0)
            # Find first Monday
            while next_month.weekday() != 0:
                next_month += timedelta(days=1)
            return next_month
            
        elif schedule.frequency == DeliveryFrequency.CUSTOM_CRON:
            if schedule.cron_expression:
                cron = croniter.croniter(schedule.cron_expression, now)
                return cron.get_next(datetime)
        
        return now + timedelta(days=1)  # Default fallback
    
    async def _schedule_delivery(self, schedule: DeliverySchedule):
        """Schedule delivery in job scheduler"""
        
        if not schedule.enabled:
            return
        
        job_id = f"delivery_{schedule.schedule_id}"
        
        # Remove existing job if any
        try:
            self.scheduler.remove_job(job_id)
        except:
            pass
        
        # Create trigger based on frequency
        if schedule.frequency == DeliveryFrequency.CUSTOM_CRON and schedule.cron_expression:
            trigger = CronTrigger.from_crontab(schedule.cron_expression)
        elif schedule.frequency == DeliveryFrequency.DAILY:
            trigger = CronTrigger(hour=8, minute=0)  # Daily at 8 AM
        elif schedule.frequency == DeliveryFrequency.WEEKLY:
            trigger = CronTrigger(day_of_week=0, hour=8, minute=0)  # Monday at 8 AM
        elif schedule.frequency == DeliveryFrequency.MONTHLY:
            trigger = CronTrigger(day=1, hour=8, minute=0)  # First of month at 8 AM
        elif schedule.frequency == DeliveryFrequency.HOURLY:
            trigger = IntervalTrigger(hours=1)
        else:
            return  # Skip immediate deliveries
        
        # Add job to scheduler
        self.scheduler.add_job(
            func=self.execute_scheduled_delivery,
            trigger=trigger,
            args=[schedule.schedule_id],
            id=job_id,
            name=f"Delivery: {schedule.name}",
            misfire_grace_time=300,  # 5 minutes grace time
            coalesce=True,  # Coalesce missed executions
            max_instances=1  # Only one instance at a time
        )
        
        logger.info(f"Scheduled delivery job: {schedule.name} ({schedule.frequency.value})")
    
    def _validate_schedule(self, schedule: DeliverySchedule) -> Dict[str, Any]:
        """Validate delivery schedule configuration"""
        
        errors = []
        warnings = []
        
        # Check required fields
        if not schedule.name:
            errors.append("Schedule name is required")
        
        if not schedule.recipients:
            errors.append("At least one recipient is required")
        
        # Validate email addresses
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in schedule.recipients:
            if not re.match(email_pattern, email):
                errors.append(f"Invalid email address: {email}")
        
        # Validate CRON expression
        if schedule.frequency == DeliveryFrequency.CUSTOM_CRON:
            if not schedule.cron_expression:
                errors.append("CRON expression is required for custom frequency")
            else:
                try:
                    croniter.croniter(schedule.cron_expression)
                except:
                    errors.append("Invalid CRON expression")
        
        # Check template existence
        if schedule.template_id:
            # Would validate template exists
            pass
        
        if schedule.report_template_id:
            # Would validate report template exists
            pass
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def get_delivery_schedules(self, active_only: bool = True) -> List[DeliverySchedule]:
        """Get delivery schedules"""
        
        if active_only:
            return [s for s in self.delivery_schedules if s.enabled]
        return self.delivery_schedules.copy()
    
    async def get_delivery_history(self, 
                                 schedule_id: Optional[str] = None,
                                 days: int = 30) -> List[ScheduledDelivery]:
        """Get delivery history"""
        
        # Query delivery history from database
        # For now, return empty list
        return []

# Factory function
def create_delivery_scheduler(db: Session, **services) -> DeliveryScheduler:
    """Create and configure delivery scheduler"""
    return DeliveryScheduler(db=db, **services)