# QMS Analytics Events System - Phase B Sprint 1 Day 2
# Event-driven analytics collection for real-time metrics

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

class AnalyticsEventType(Enum):
    """Types of analytics events that can be triggered"""
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_APPROVED = "document_approved"
    DOCUMENT_ACCESSED = "document_accessed"
    TRAINING_ASSIGNED = "training_assigned"
    TRAINING_COMPLETED = "training_completed"
    TRAINING_OVERDUE = "training_overdue"
    QUALITY_EVENT_CREATED = "quality_event_created"
    QUALITY_EVENT_RESOLVED = "quality_event_resolved"
    CAPA_CREATED = "capa_created"
    CAPA_COMPLETED = "capa_completed"
    USER_LOGIN = "user_login"
    USER_ACTIVITY = "user_activity"
    LIMS_TEST_CREATED = "lims_test_created"
    LIMS_TEST_COMPLETED = "lims_test_completed"

@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_type: AnalyticsEventType
    entity_type: str
    entity_id: int
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    module_name: str = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

class AnalyticsEventBus:
    """Event bus for collecting and processing analytics events"""
    
    def __init__(self, analytics_service):
        self.analytics_service = analytics_service
        self.event_handlers = {
            AnalyticsEventType.DOCUMENT_CREATED: self._handle_document_created,
            AnalyticsEventType.DOCUMENT_APPROVED: self._handle_document_approved,
            AnalyticsEventType.TRAINING_COMPLETED: self._handle_training_completed,
            AnalyticsEventType.QUALITY_EVENT_CREATED: self._handle_quality_event_created,
            AnalyticsEventType.QUALITY_EVENT_RESOLVED: self._handle_quality_event_resolved,
            AnalyticsEventType.USER_LOGIN: self._handle_user_login,
        }
    
    def emit_event(self, event: AnalyticsEvent) -> bool:
        """Emit an analytics event for processing"""
        try:
            handler = self.event_handlers.get(event.event_type)
            if handler:
                return handler(event)
            else:
                print(f"No handler for event type: {event.event_type}")
                return False
        except Exception as e:
            print(f"Error processing analytics event: {e}")
            return False
    
    def _handle_document_created(self, event: AnalyticsEvent) -> bool:
        """Handle document creation analytics"""
        return self.analytics_service.store_metric(
            metric_name="Documents Created",
            metric_category="documents",
            value=1,
            unit="count",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="edms",
            calculation_method="event_count",
            data_source="document_events"
        )
    
    def _handle_document_approved(self, event: AnalyticsEvent) -> bool:
        """Handle document approval analytics"""
        approval_time = event.metadata.get('approval_time_days', 0)
        
        return self.analytics_service.store_metric(
            metric_name="Average Approval Time",
            metric_category="documents",
            value=approval_time,
            unit="days",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="edms"
        )
    
    def _handle_training_completed(self, event: AnalyticsEvent) -> bool:
        """Handle training completion analytics"""
        score = event.metadata.get('score', 0)
        hours = event.metadata.get('duration_hours', 0)
        
        success = self.analytics_service.store_metric(
            metric_name="Training Completed",
            metric_category="training",
            value=1,
            unit="count",
            department_id=event.department_id,
            user_id=event.user_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="tms"
        )
        
        if score > 0:
            self.analytics_service.store_metric(
                metric_name="Average Training Score",
                metric_category="training",
                value=score,
                unit="score",
                department_id=event.department_id,
                user_id=event.user_id,
                module_name="tms"
            )
        
        return success
    
    def _handle_quality_event_created(self, event: AnalyticsEvent) -> bool:
        """Handle quality event creation analytics"""
        return self.analytics_service.store_metric(
            metric_name="Quality Events Count",
            metric_category="quality",
            value=1,
            unit="count",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="qrm"
        )
    
    def _handle_quality_event_resolved(self, event: AnalyticsEvent) -> bool:
        """Handle quality event resolution analytics"""
        resolution_time = event.metadata.get('resolution_time_days', 0)
        
        return self.analytics_service.store_metric(
            metric_name="Average Resolution Time",
            metric_category="quality",
            value=resolution_time,
            unit="days",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="qrm"
        )
    
    def _handle_user_login(self, event: AnalyticsEvent) -> bool:
        """Handle user login analytics"""
        return self.analytics_service.store_metric(
            metric_name="User Logins",
            metric_category="organizational",
            value=1,
            unit="count",
            department_id=event.department_id,
            user_id=event.user_id,
            module_name="organization"
        )

# Global event bus instance
_event_bus_instance = None

def get_analytics_event_bus(analytics_service=None):
    """Get or create the global analytics event bus"""
    global _event_bus_instance
    if _event_bus_instance is None and analytics_service:
        _event_bus_instance = AnalyticsEventBus(analytics_service)
    return _event_bus_instance

def emit_analytics_event(event_type: AnalyticsEventType, entity_type: str, entity_id: int,
                        user_id: Optional[int] = None, department_id: Optional[int] = None,
                        module_name: str = None, metadata: Dict[str, Any] = None) -> bool:
    """Convenience function to emit analytics events"""
    event_bus = get_analytics_event_bus()
    if event_bus:
        event = AnalyticsEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            department_id=department_id,
            module_name=module_name,
            metadata=metadata or {}
        )
        return event_bus.emit_event(event)
    return False