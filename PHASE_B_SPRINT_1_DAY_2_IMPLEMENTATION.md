# 🔧 Phase B Sprint 1 Day 2 - Service Integration & Testing

**Phase**: B - Advanced Reporting & Analytics  
**Sprint**: 1 - Analytics Foundation & Data Model  
**Day**: 2 - Service Integration & Testing  
**Focus**: Connecting analytics with existing QMS modules and comprehensive validation

---

## 🎯 **Day 2 Objectives**

### **Primary Goals:**
- [ ] Integrate analytics service with existing QMS modules (EDMS, TMS, QRM, LIMS)
- [ ] Create automatic metrics collection from module operations
- [ ] Test analytics APIs with real data
- [ ] Validate performance with actual workloads
- [ ] Implement real-time metrics updates
- [ ] Create integration test suite for end-to-end validation

### **Deliverables:**
- Module integration adapters for automatic metrics collection
- Real-time metrics collection system
- Comprehensive integration test suite
- Performance validation report
- Analytics data flow documentation

---

## 🔗 **Integration Architecture Plan**

### **QMS Module Integration Points:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    QMS Analytics Integration                     │
├─────────────────────────────────────────────────────────────────┤
│  EDMS Module     │  TMS Module      │  QRM Module     │  LIMS    │
│  ├─ Documents    │  ├─ Training     │  ├─ Quality     │  ├─ Tests│
│  ├─ Workflows    │  ├─ Assignments  │  ├─ Events      │  ├─ Data │
│  └─ Approvals    │  └─ Compliance   │  └─ CAPAs       │  └─ QC   │
├─────────────────────────────────────────────────────────────────┤
│                     Analytics Events Bus                        │
├─────────────────────────────────────────────────────────────────┤
│                     Analytics Service                           │
│  ├─ Metrics Collection    ├─ Data Aggregation                  │
│  ├─ Real-time Updates     ├─ Performance Caching               │
│  └─ Dashboard Generation  └─ Report Processing                 │
├─────────────────────────────────────────────────────────────────┤
│                     Analytics Database                          │
│  └─ Metrics Storage, Caching, Reports, Dashboards              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Module Integration Implementation**

### **1. Analytics Event System**

#### **Event Bus for Real-time Metrics**
```python
# backend/app/services/analytics/analytics_events.py
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
    
    def __init__(self, analytics_service: 'AnalyticsService'):
        self.analytics_service = analytics_service
        self.event_handlers = {
            AnalyticsEventType.DOCUMENT_CREATED: self._handle_document_created,
            AnalyticsEventType.DOCUMENT_APPROVED: self._handle_document_approved,
            AnalyticsEventType.DOCUMENT_ACCESSED: self._handle_document_accessed,
            AnalyticsEventType.TRAINING_COMPLETED: self._handle_training_completed,
            AnalyticsEventType.TRAINING_OVERDUE: self._handle_training_overdue,
            AnalyticsEventType.QUALITY_EVENT_CREATED: self._handle_quality_event_created,
            AnalyticsEventType.QUALITY_EVENT_RESOLVED: self._handle_quality_event_resolved,
            AnalyticsEventType.USER_LOGIN: self._handle_user_login,
            AnalyticsEventType.LIMS_TEST_COMPLETED: self._handle_lims_test_completed,
        }
    
    def emit_event(self, event: AnalyticsEvent) -> bool:
        """Emit an analytics event for processing"""
        try:
            handler = self.event_handlers.get(event.event_type)
            if handler:
                return handler(event)
            else:
                # Log unknown event type
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
        
        # Store approval time metric
        success1 = self.analytics_service.store_metric(
            metric_name="Average Approval Time",
            metric_category="documents",
            value=approval_time,
            unit="days",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="edms"
        )
        
        # Store approval count
        success2 = self.analytics_service.store_metric(
            metric_name="Documents Approved",
            metric_category="documents",
            value=1,
            unit="count",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="edms"
        )
        
        return success1 and success2
    
    def _handle_training_completed(self, event: AnalyticsEvent) -> bool:
        """Handle training completion analytics"""
        score = event.metadata.get('score', 0)
        hours = event.metadata.get('duration_hours', 0)
        
        metrics_stored = []
        
        # Store completion count
        metrics_stored.append(self.analytics_service.store_metric(
            metric_name="Training Completed",
            metric_category="training",
            value=1,
            unit="count",
            department_id=event.department_id,
            user_id=event.user_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="tms"
        ))
        
        # Store score if available
        if score > 0:
            metrics_stored.append(self.analytics_service.store_metric(
                metric_name="Average Training Score",
                metric_category="training",
                value=score,
                unit="score",
                department_id=event.department_id,
                user_id=event.user_id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                module_name="tms"
            ))
        
        # Store hours if available
        if hours > 0:
            metrics_stored.append(self.analytics_service.store_metric(
                metric_name="Training Hours Completed",
                metric_category="training",
                value=hours,
                unit="hours",
                department_id=event.department_id,
                user_id=event.user_id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                module_name="tms"
            ))
        
        return all(metrics_stored)
    
    def _handle_quality_event_created(self, event: AnalyticsEvent) -> bool:
        """Handle quality event creation analytics"""
        severity = event.metadata.get('severity', 'medium')
        
        return self.analytics_service.store_metric(
            metric_name="Quality Events Count",
            metric_category="quality",
            value=1,
            unit="count",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="qrm",
            subcategory=severity,
            calculation_method="event_count"
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
            module_name="qrm",
            calculation_method="resolution_time"
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
            entity_type="user_session",
            entity_id=event.entity_id,
            module_name="organization"
        )
    
    def _handle_lims_test_completed(self, event: AnalyticsEvent) -> bool:
        """Handle LIMS test completion analytics"""
        test_result = event.metadata.get('result', 'unknown')
        duration_hours = event.metadata.get('duration_hours', 0)
        
        metrics_stored = []
        
        # Store test completion count
        metrics_stored.append(self.analytics_service.store_metric(
            metric_name="Tests Completed",
            metric_category="quality",
            value=1,
            unit="count",
            department_id=event.department_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            module_name="lims",
            subcategory=test_result
        ))
        
        # Store test duration
        if duration_hours > 0:
            metrics_stored.append(self.analytics_service.store_metric(
                metric_name="Average Test Duration",
                metric_category="quality",
                value=duration_hours,
                unit="hours",
                department_id=event.department_id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                module_name="lims"
            ))
        
        return all(metrics_stored)

# Global event bus instance
_event_bus_instance = None

def get_analytics_event_bus(analytics_service: 'AnalyticsService' = None) -> AnalyticsEventBus:
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
```

### **2. Module Integration Adapters**

#### **EDMS Integration Adapter**
```python
# backend/app/services/analytics/integrations/edms_integration.py
from app.services.analytics.analytics_events import emit_analytics_event, AnalyticsEventType
from datetime import datetime
from typing import Optional

class EDMSAnalyticsIntegration:
    """Integration adapter for EDMS module analytics"""
    
    @staticmethod
    def on_document_created(document_id: int, user_id: int, department_id: Optional[int] = None):
        """Called when a document is created"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.DOCUMENT_CREATED,
            entity_type="document",
            entity_id=document_id,
            user_id=user_id,
            department_id=department_id,
            module_name="edms"
        )
    
    @staticmethod
    def on_document_approved(document_id: int, user_id: int, department_id: Optional[int] = None,
                           approval_time_days: float = 0):
        """Called when a document is approved"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.DOCUMENT_APPROVED,
            entity_type="document",
            entity_id=document_id,
            user_id=user_id,
            department_id=department_id,
            module_name="edms",
            metadata={"approval_time_days": approval_time_days}
        )
    
    @staticmethod
    def on_document_accessed(document_id: int, user_id: int, department_id: Optional[int] = None):
        """Called when a document is accessed"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.DOCUMENT_ACCESSED,
            entity_type="document",
            entity_id=document_id,
            user_id=user_id,
            department_id=department_id,
            module_name="edms"
        )
```

#### **TMS Integration Adapter**
```python
# backend/app/services/analytics/integrations/tms_integration.py
from app.services.analytics.analytics_events import emit_analytics_event, AnalyticsEventType
from typing import Optional

class TMSAnalyticsIntegration:
    """Integration adapter for Training Management System analytics"""
    
    @staticmethod
    def on_training_assigned(assignment_id: int, user_id: int, program_id: int,
                           department_id: Optional[int] = None):
        """Called when training is assigned to a user"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.TRAINING_ASSIGNED,
            entity_type="training_assignment",
            entity_id=assignment_id,
            user_id=user_id,
            department_id=department_id,
            module_name="tms",
            metadata={"program_id": program_id}
        )
    
    @staticmethod
    def on_training_completed(assignment_id: int, user_id: int, department_id: Optional[int] = None,
                            score: Optional[float] = None, duration_hours: Optional[float] = None):
        """Called when training is completed"""
        metadata = {}
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
                          days_overdue: int = 0):
        """Called when training becomes overdue"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.TRAINING_OVERDUE,
            entity_type="training_assignment",
            entity_id=assignment_id,
            user_id=user_id,
            department_id=department_id,
            module_name="tms",
            metadata={"days_overdue": days_overdue}
        )
```

#### **QRM Integration Adapter**
```python
# backend/app/services/analytics/integrations/qrm_integration.py
from app.services.analytics.analytics_events import emit_analytics_event, AnalyticsEventType
from typing import Optional

class QRMAnalyticsIntegration:
    """Integration adapter for Quality Risk Management analytics"""
    
    @staticmethod
    def on_quality_event_created(event_id: int, user_id: int, department_id: Optional[int] = None,
                               severity: str = "medium", event_type: str = "deviation"):
        """Called when a quality event is created"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.QUALITY_EVENT_CREATED,
            entity_type="quality_event",
            entity_id=event_id,
            user_id=user_id,
            department_id=department_id,
            module_name="qrm",
            metadata={"severity": severity, "event_type": event_type}
        )
    
    @staticmethod
    def on_quality_event_resolved(event_id: int, user_id: int, department_id: Optional[int] = None,
                                resolution_time_days: float = 0):
        """Called when a quality event is resolved"""
        return emit_analytics_event(
            event_type=AnalyticsEventType.QUALITY_EVENT_RESOLVED,
            entity_type="quality_event",
            entity_id=event_id,
            user_id=user_id,
            department_id=department_id,
            module_name="qrm",
            metadata={"resolution_time_days": resolution_time_days}
        )
    
    @staticmethod
    def on_capa_created(capa_id: int, user_id: int, department_id: Optional[int] = None,
                       quality_event_id: Optional[int] = None):
        """Called when a CAPA is created"""
        metadata = {}
        if quality_event_id:
            metadata["quality_event_id"] = quality_event_id
            
        return emit_analytics_event(
            event_type=AnalyticsEventType.CAPA_CREATED,
            entity_type="capa",
            entity_id=capa_id,
            user_id=user_id,
            department_id=department_id,
            module_name="qrm",
            metadata=metadata
        )
    
    @staticmethod
    def on_capa_completed(capa_id: int, user_id: int, department_id: Optional[int] = None,
                        effectiveness_score: Optional[float] = None):
        """Called when a CAPA is completed"""
        metadata = {}
        if effectiveness_score is not None:
            metadata["effectiveness_score"] = effectiveness_score
            
        return emit_analytics_event(
            event_type=AnalyticsEventType.CAPA_COMPLETED,
            entity_type="capa",
            entity_id=capa_id,
            user_id=user_id,
            department_id=department_id,
            module_name="qrm",
            metadata=metadata
        )
```

---

## 🧪 **Comprehensive Integration Testing**

Let me continue with the testing framework and validation system...