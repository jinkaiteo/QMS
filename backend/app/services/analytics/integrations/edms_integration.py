# EDMS Analytics Integration - Phase B Sprint 1 Day 2
# Integration adapter for Electronic Document Management System analytics

from app.services.analytics.analytics_events import emit_analytics_event, AnalyticsEventType
from datetime import datetime
from typing import Optional

class EDMSAnalyticsIntegration:
    """Integration adapter for EDMS module analytics"""
    
    @staticmethod
    def on_document_created(document_id: int, user_id: int, department_id: Optional[int] = None,
                          document_type: str = "standard"):
        """Called when a document is created"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.DOCUMENT_CREATED,
            entity_type="document",
            entity_id=document_id,
            user_id=user_id,
            department_id=department_id,
            module_name="edms",
            metadata={"document_type": document_type}
        )
    
    @staticmethod
    def on_document_approved(document_id: int, user_id: int, department_id: Optional[int] = None,
                           approval_time_days: float = 0, workflow_stage: str = "final"):
        """Called when a document is approved"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.DOCUMENT_APPROVED,
            entity_type="document",
            entity_id=document_id,
            user_id=user_id,
            department_id=department_id,
            module_name="edms",
            metadata={
                "approval_time_days": approval_time_days,
                "workflow_stage": workflow_stage
            }
        )
    
    @staticmethod
    def on_document_accessed(document_id: int, user_id: int, department_id: Optional[int] = None,
                           access_type: str = "view"):
        """Called when a document is accessed"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.DOCUMENT_ACCESSED,
            entity_type="document",
            entity_id=document_id,
            user_id=user_id,
            department_id=department_id,
            module_name="edms",
            metadata={"access_type": access_type}
        )
    
    @staticmethod
    def on_document_revised(document_id: int, user_id: int, department_id: Optional[int] = None,
                          revision_reason: str = "update"):
        """Called when a document is revised"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.DOCUMENT_CREATED,  # Reuse for revision tracking
            entity_type="document_revision",
            entity_id=document_id,
            user_id=user_id,
            department_id=department_id,
            module_name="edms",
            metadata={"revision_reason": revision_reason}
        )