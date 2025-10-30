# TMS Analytics Integration - Phase B Sprint 1 Day 2
# Integration adapter for Training Management System analytics

from app.services.analytics.analytics_events import emit_analytics_event, AnalyticsEventType
from typing import Optional

class TMSAnalyticsIntegration:
    """Integration adapter for Training Management System analytics"""
    
    @staticmethod
    def on_training_assigned(assignment_id: int, user_id: int, program_id: int,
                           department_id: Optional[int] = None, due_date: str = None):
        """Called when training is assigned to a user"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.TRAINING_ASSIGNED,
            entity_type="training_assignment",
            entity_id=assignment_id,
            user_id=user_id,
            department_id=department_id,
            module_name="tms",
            metadata={
                "program_id": program_id,
                "due_date": due_date
            }
        )
    
    @staticmethod
    def on_training_completed(assignment_id: int, user_id: int, department_id: Optional[int] = None,
                            score: Optional[float] = None, duration_hours: Optional[float] = None,
                            completion_status: str = "completed"):
        """Called when training is completed"""
        metadata = {
            "completion_status": completion_status
        }
        if score is not None:
            metadata["score"] = score
        if duration_hours is not None:
            metadata["duration_hours"] = duration_hours
            
        return emit_analytics_event(
            event_type=AnalyticsEventType.TRAINING_COMPLETED,
            entity_type="training_assignment",
            entity_id=assignment_id,
            user_id=user_id,
            department_id=department_id,
            module_name="tms",
            metadata=metadata
        )
    
    @staticmethod
    def on_training_overdue(assignment_id: int, user_id: int, department_id: Optional[int] = None,
                          days_overdue: int = 0, program_type: str = "mandatory"):
        """Called when training becomes overdue"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.TRAINING_OVERDUE,
            entity_type="training_assignment",
            entity_id=assignment_id,
            user_id=user_id,
            department_id=department_id,
            module_name="tms",
            metadata={
                "days_overdue": days_overdue,
                "program_type": program_type
            }
        )
    
    @staticmethod
    def on_training_started(assignment_id: int, user_id: int, department_id: Optional[int] = None,
                          start_method: str = "online"):
        """Called when training is started"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.USER_ACTIVITY,  # Use general activity event
            entity_type="training_session",
            entity_id=assignment_id,
            user_id=user_id,
            department_id=department_id,
            module_name="tms",
            metadata={
                "activity_type": "training_started",
                "start_method": start_method
            }
        )