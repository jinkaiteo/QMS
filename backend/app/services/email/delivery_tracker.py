# Delivery Tracker Service - Phase B Sprint 2 Day 5
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class DeliveryStatus(Enum):
    """Email delivery status tracking"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"
    SPAM = "spam"
    UNSUBSCRIBED = "unsubscribed"

@dataclass
class DeliveryTracking:
    """Email delivery tracking record"""
    tracking_id: str
    message_id: str
    recipient_email: str
    status: DeliveryStatus
    scheduled_time: datetime
    sent_time: Optional[datetime] = None
    delivered_time: Optional[datetime] = None
    opened_time: Optional[datetime] = None
    clicked_time: Optional[datetime] = None
    failed_time: Optional[datetime] = None
    bounce_reason: Optional[str] = None
    error_message: Optional[str] = None
    smtp_response: Optional[str] = None
    retry_count: int = 0
    last_retry: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeliveryStats:
    """Delivery statistics summary"""
    total_sent: int
    delivered: int
    opened: int
    clicked: int
    failed: int
    bounced: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float
    period_start: datetime
    period_end: datetime

class DeliveryTracker:
    """
    Email Delivery Tracking Service
    Comprehensive delivery status monitoring and analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Tracking configuration
        self.track_opens = True
        self.track_clicks = True
        self.retention_days = 90
        
    async def track_delivery(self, delivery_result: Any) -> str:
        """Track email delivery result"""
        
        from .email_service import EmailDeliveryResult, DeliveryStatus as EmailDeliveryStatus
        
        # Generate tracking ID
        tracking_id = f"track_{delivery_result.message_id}_{int(datetime.now().timestamp())}"
        
        # Map email service status to tracking status
        status_mapping = {
            EmailDeliveryStatus.PENDING: DeliveryStatus.PENDING,
            EmailDeliveryStatus.QUEUED: DeliveryStatus.QUEUED,
            EmailDeliveryStatus.SENDING: DeliveryStatus.SENDING,
            EmailDeliveryStatus.SENT: DeliveryStatus.SENT,
            EmailDeliveryStatus.DELIVERED: DeliveryStatus.DELIVERED,
            EmailDeliveryStatus.FAILED: DeliveryStatus.FAILED,
            EmailDeliveryStatus.BOUNCED: DeliveryStatus.BOUNCED,
            EmailDeliveryStatus.REJECTED: DeliveryStatus.REJECTED
        }
        
        tracking_status = status_mapping.get(delivery_result.status, DeliveryStatus.PENDING)
        
        # Create tracking record
        tracking = DeliveryTracking(
            tracking_id=tracking_id,
            message_id=delivery_result.message_id,
            recipient_email="",  # Would be provided by email service
            status=tracking_status,
            scheduled_time=datetime.now(),
            sent_time=delivery_result.delivered_at,
            error_message=delivery_result.error_message,
            smtp_response=delivery_result.smtp_response,
            retry_count=delivery_result.retry_count
        )
        
        # Store tracking record
        await self._store_tracking_record(tracking)
        
        logger.debug(f"Delivery tracked: {tracking_id} - {tracking_status.value}")
        
        return tracking_id
    
    async def update_delivery_status(self, 
                                   tracking_id: str,
                                   status: DeliveryStatus,
                                   metadata: Dict[str, Any] = None) -> bool:
        """Update delivery tracking status"""
        
        try:
            # Get existing tracking record
            tracking = await self._get_tracking_record(tracking_id)
            if not tracking:
                logger.warning(f"Tracking record not found: {tracking_id}")
                return False
            
            # Update status and timestamps
            tracking.status = status
            
            if status == DeliveryStatus.DELIVERED and not tracking.delivered_time:
                tracking.delivered_time = datetime.now()
            elif status == DeliveryStatus.OPENED and not tracking.opened_time:
                tracking.opened_time = datetime.now()
            elif status == DeliveryStatus.CLICKED and not tracking.clicked_time:
                tracking.clicked_time = datetime.now()
            elif status in [DeliveryStatus.FAILED, DeliveryStatus.BOUNCED] and not tracking.failed_time:
                tracking.failed_time = datetime.now()
            
            # Update metadata
            if metadata:
                tracking.metadata.update(metadata)
            
            # Store updated record
            await self._store_tracking_record(tracking)
            
            logger.debug(f"Delivery status updated: {tracking_id} - {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update delivery status: {str(e)}")
            return False
    
    async def get_delivery_tracking(self, tracking_id: str) -> Optional[DeliveryTracking]:
        """Get delivery tracking by ID"""
        return await self._get_tracking_record(tracking_id)
    
    async def get_message_tracking(self, message_id: str) -> List[DeliveryTracking]:
        """Get all tracking records for a message"""
        
        try:
            query = """
                SELECT * FROM email_delivery_tracking
                WHERE message_id = :message_id
                ORDER BY scheduled_time DESC
            """
            
            result = self.db.execute(text(query), {'message_id': message_id})
            tracking_records = []
            
            for row in result.fetchall():
                tracking = self._row_to_tracking(row)
                tracking_records.append(tracking)
            
            return tracking_records
            
        except Exception as e:
            logger.error(f"Failed to get message tracking: {str(e)}")
            return []
    
    async def get_delivery_stats(self, 
                                start_date: datetime,
                                end_date: datetime,
                                recipient_filter: Optional[str] = None) -> DeliveryStats:
        """Get delivery statistics for date range"""
        
        try:
            # Build query with optional recipient filter
            where_clause = "WHERE scheduled_time BETWEEN :start_date AND :end_date"
            params = {'start_date': start_date, 'end_date': end_date}
            
            if recipient_filter:
                where_clause += " AND recipient_email LIKE :recipient_filter"
                params['recipient_filter'] = f"%{recipient_filter}%"
            
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered,
                    COUNT(CASE WHEN status = 'opened' THEN 1 END) as opened,
                    COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'bounced' THEN 1 END) as bounced
                FROM email_delivery_tracking
                {where_clause}
            """
            
            result = self.db.execute(text(stats_query), params)
            stats_data = dict(zip(result.keys(), result.fetchone() or [0]*6))
            
            # Calculate rates
            total_sent = stats_data.get('total_sent', 0)
            delivered = stats_data.get('delivered', 0)
            opened = stats_data.get('opened', 0)
            clicked = stats_data.get('clicked', 0)
            failed = stats_data.get('failed', 0)
            bounced = stats_data.get('bounced', 0)
            
            delivery_rate = (delivered / max(total_sent, 1)) * 100
            open_rate = (opened / max(delivered, 1)) * 100
            click_rate = (clicked / max(opened, 1)) * 100
            bounce_rate = (bounced / max(total_sent, 1)) * 100
            
            return DeliveryStats(
                total_sent=total_sent,
                delivered=delivered,
                opened=opened,
                clicked=clicked,
                failed=failed,
                bounced=bounced,
                delivery_rate=round(delivery_rate, 2),
                open_rate=round(open_rate, 2),
                click_rate=round(click_rate, 2),
                bounce_rate=round(bounce_rate, 2),
                period_start=start_date,
                period_end=end_date
            )
            
        except Exception as e:
            logger.error(f"Failed to get delivery stats: {str(e)}")
            return DeliveryStats(
                total_sent=0, delivered=0, opened=0, clicked=0, failed=0, bounced=0,
                delivery_rate=0.0, open_rate=0.0, click_rate=0.0, bounce_rate=0.0,
                period_start=start_date, period_end=end_date
            )
    
    async def get_failed_deliveries(self, 
                                  days: int = 7,
                                  retry_eligible: bool = True) -> List[DeliveryTracking]:
        """Get failed deliveries for retry or analysis"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            where_clause = """
                WHERE status IN ('failed', 'bounced', 'rejected')
                AND scheduled_time >= :cutoff_date
            """
            
            if retry_eligible:
                where_clause += " AND retry_count < 3"
            
            query = f"""
                SELECT * FROM email_delivery_tracking
                {where_clause}
                ORDER BY scheduled_time DESC
            """
            
            result = self.db.execute(text(query), {'cutoff_date': cutoff_date})
            failed_deliveries = []
            
            for row in result.fetchall():
                tracking = self._row_to_tracking(row)
                failed_deliveries.append(tracking)
            
            return failed_deliveries
            
        except Exception as e:
            logger.error(f"Failed to get failed deliveries: {str(e)}")
            return []
    
    async def cleanup_old_tracking_data(self) -> int:
        """Clean up old tracking data beyond retention period"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            delete_query = """
                DELETE FROM email_delivery_tracking
                WHERE scheduled_time < :cutoff_date
            """
            
            result = self.db.execute(text(delete_query), {'cutoff_date': cutoff_date})
            self.db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} old tracking records")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup tracking data: {str(e)}")
            self.db.rollback()
            return 0
    
    async def _store_tracking_record(self, tracking: DeliveryTracking):
        """Store tracking record in database"""
        
        try:
            upsert_query = """
                INSERT INTO email_delivery_tracking 
                (tracking_id, message_id, recipient_email, status, scheduled_time,
                 sent_time, delivered_time, opened_time, clicked_time, failed_time,
                 bounce_reason, error_message, smtp_response, retry_count, last_retry, metadata)
                VALUES (:tracking_id, :message_id, :recipient_email, :status, :scheduled_time,
                        :sent_time, :delivered_time, :opened_time, :clicked_time, :failed_time,
                        :bounce_reason, :error_message, :smtp_response, :retry_count, :last_retry, :metadata)
                ON CONFLICT (tracking_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    sent_time = EXCLUDED.sent_time,
                    delivered_time = EXCLUDED.delivered_time,
                    opened_time = EXCLUDED.opened_time,
                    clicked_time = EXCLUDED.clicked_time,
                    failed_time = EXCLUDED.failed_time,
                    bounce_reason = EXCLUDED.bounce_reason,
                    error_message = EXCLUDED.error_message,
                    smtp_response = EXCLUDED.smtp_response,
                    retry_count = EXCLUDED.retry_count,
                    last_retry = EXCLUDED.last_retry,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """
            
            self.db.execute(text(upsert_query), {
                'tracking_id': tracking.tracking_id,
                'message_id': tracking.message_id,
                'recipient_email': tracking.recipient_email,
                'status': tracking.status.value,
                'scheduled_time': tracking.scheduled_time,
                'sent_time': tracking.sent_time,
                'delivered_time': tracking.delivered_time,
                'opened_time': tracking.opened_time,
                'clicked_time': tracking.clicked_time,
                'failed_time': tracking.failed_time,
                'bounce_reason': tracking.bounce_reason,
                'error_message': tracking.error_message,
                'smtp_response': tracking.smtp_response,
                'retry_count': tracking.retry_count,
                'last_retry': tracking.last_retry,
                'metadata': json.dumps(tracking.metadata) if tracking.metadata else None
            })
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store tracking record: {str(e)}")
            self.db.rollback()
            raise e
    
    async def _get_tracking_record(self, tracking_id: str) -> Optional[DeliveryTracking]:
        """Get tracking record from database"""
        
        try:
            query = """
                SELECT * FROM email_delivery_tracking
                WHERE tracking_id = :tracking_id
            """
            
            result = self.db.execute(text(query), {'tracking_id': tracking_id})
            row = result.fetchone()
            
            if row:
                return self._row_to_tracking(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tracking record: {str(e)}")
            return None
    
    def _row_to_tracking(self, row) -> DeliveryTracking:
        """Convert database row to DeliveryTracking object"""
        
        metadata = {}
        if row.metadata:
            try:
                metadata = json.loads(row.metadata)
            except:
                pass
        
        return DeliveryTracking(
            tracking_id=row.tracking_id,
            message_id=row.message_id,
            recipient_email=row.recipient_email,
            status=DeliveryStatus(row.status),
            scheduled_time=row.scheduled_time,
            sent_time=row.sent_time,
            delivered_time=row.delivered_time,
            opened_time=row.opened_time,
            clicked_time=row.clicked_time,
            failed_time=row.failed_time,
            bounce_reason=row.bounce_reason,
            error_message=row.error_message,
            smtp_response=row.smtp_response,
            retry_count=row.retry_count or 0,
            last_retry=row.last_retry,
            metadata=metadata
        )

# Factory function
def create_delivery_tracker(db: Session) -> DeliveryTracker:
    """Create and configure delivery tracker"""
    return DeliveryTracker(db=db)