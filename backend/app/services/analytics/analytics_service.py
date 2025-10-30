# QMS Analytics Service - Phase B Sprint 1 Day 1
# Core analytics service for metrics collection, aggregation, and reporting

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from app.models.user import User
from app.models.organization_management.department_hierarchy import Department
from app.core.database import get_db
import json
import hashlib
from decimal import Decimal

class AnalyticsService:
    """
    Core analytics service that handles metrics collection, aggregation,
    and data preparation for dashboards and reports.
    """
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        
    # ========================================
    # METRICS COLLECTION METHODS
    # ========================================
    
    def collect_quality_metrics(self, department_id: Optional[int] = None, 
                              period_days: int = 30) -> Dict[str, Any]:
        """
        Collect quality-related metrics for analytics and dashboards.
        
        Args:
            department_id: Filter by specific department (None for all)
            period_days: Number of days to analyze
            
        Returns:
            Dictionary containing quality metrics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Base query for analytics metrics
        base_query = self.db.query(text("""
            SELECT 
                metric_name,
                metric_subcategory,
                AVG(value) as avg_value,
                MAX(value) as max_value,
                MIN(value) as min_value,
                COUNT(*) as measurement_count,
                MAX(measurement_date) as latest_measurement
            FROM analytics_metrics 
            WHERE metric_category = 'quality'
            AND is_deleted = FALSE
            AND measurement_date >= :start_date
            AND measurement_date <= :end_date
        """))
        
        # Add department filter if specified
        if department_id:
            base_query = base_query.filter(text("department_id = :dept_id"))
            
        query_params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        if department_id:
            query_params['dept_id'] = department_id
            
        base_query = base_query.params(**query_params)
        base_query = base_query.group_by(text("metric_name, metric_subcategory"))
        
        results = base_query.all()
        
        quality_metrics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'department_id': department_id,
            'metrics': {},
            'summary': {
                'total_measurements': 0,
                'unique_metrics': 0,
                'latest_update': None
            }
        }
        
        for row in results:
            metric_key = f"{row.metric_name}_{row.metric_subcategory}" if row.metric_subcategory else row.metric_name
            quality_metrics['metrics'][metric_key] = {
                'name': row.metric_name,
                'subcategory': row.metric_subcategory,
                'average': float(row.avg_value) if row.avg_value else 0,
                'maximum': float(row.max_value) if row.max_value else 0,
                'minimum': float(row.min_value) if row.min_value else 0,
                'measurement_count': row.measurement_count,
                'latest_measurement': row.latest_measurement.isoformat() if row.latest_measurement else None
            }
            quality_metrics['summary']['total_measurements'] += row.measurement_count
            
        quality_metrics['summary']['unique_metrics'] = len(quality_metrics['metrics'])
        
        return quality_metrics
    
    def collect_training_metrics(self, department_id: Optional[int] = None,
                               period_days: int = 30) -> Dict[str, Any]:
        """
        Collect training-related metrics for analytics and dashboards.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Training metrics query
        query = self.db.execute(text("""
            SELECT 
                metric_name,
                metric_subcategory,
                AVG(value) as avg_value,
                SUM(CASE WHEN unit = 'count' THEN value ELSE 0 END) as total_count,
                AVG(CASE WHEN unit = 'percentage' THEN value ELSE NULL END) as avg_percentage,
                AVG(CASE WHEN unit = 'hours' THEN value ELSE NULL END) as avg_hours,
                COUNT(*) as measurement_count
            FROM analytics_metrics 
            WHERE metric_category = 'training'
            AND is_deleted = FALSE
            AND measurement_date >= :start_date
            AND measurement_date <= :end_date
            {dept_filter}
            GROUP BY metric_name, metric_subcategory
        """.format(
            dept_filter="AND department_id = :dept_id" if department_id else ""
        )), {
            'start_date': start_date,
            'end_date': end_date,
            'dept_id': department_id
        })
        
        results = query.fetchall()
        
        training_metrics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'department_id': department_id,
            'completion_rate': 0,
            'total_hours': 0,
            'overdue_count': 0,
            'average_score': 0,
            'metrics_detail': {}
        }
        
        for row in results:
            metric_name = row.metric_name
            if 'Completion Rate' in metric_name:
                training_metrics['completion_rate'] = float(row.avg_percentage or 0)
            elif 'Hours Completed' in metric_name:
                training_metrics['total_hours'] = float(row.total_count or 0)
            elif 'Overdue' in metric_name:
                training_metrics['overdue_count'] = int(row.total_count or 0)
            elif 'Score' in metric_name:
                training_metrics['average_score'] = float(row.avg_value or 0)
                
            training_metrics['metrics_detail'][metric_name] = {
                'subcategory': row.metric_subcategory,
                'average': float(row.avg_value or 0),
                'total_count': int(row.total_count or 0),
                'measurement_count': row.measurement_count
            }
            
        return training_metrics
    
    def collect_document_metrics(self, department_id: Optional[int] = None,
                               period_days: int = 30) -> Dict[str, Any]:
        """
        Collect document-related metrics for analytics and dashboards.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Document metrics query
        query = self.db.execute(text("""
            SELECT 
                metric_name,
                metric_subcategory,
                SUM(CASE WHEN unit = 'count' THEN value ELSE 0 END) as total_count,
                AVG(CASE WHEN unit = 'days' THEN value ELSE NULL END) as avg_days,
                AVG(CASE WHEN unit = 'percentage' THEN value ELSE NULL END) as avg_percentage,
                COUNT(*) as measurement_count
            FROM analytics_metrics 
            WHERE metric_category = 'documents'
            AND is_deleted = FALSE
            AND measurement_date >= :start_date
            AND measurement_date <= :end_date
            {dept_filter}
            GROUP BY metric_name, metric_subcategory
        """.format(
            dept_filter="AND department_id = :dept_id" if department_id else ""
        )), {
            'start_date': start_date,
            'end_date': end_date,
            'dept_id': department_id
        })
        
        results = query.fetchall()
        
        document_metrics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'department_id': department_id,
            'documents_created': 0,
            'average_approval_time': 0,
            'total_access_count': 0,
            'revision_rate': 0,
            'metrics_detail': {}
        }
        
        for row in results:
            metric_name = row.metric_name
            if 'Created' in metric_name:
                document_metrics['documents_created'] = int(row.total_count or 0)
            elif 'Approval Time' in metric_name:
                document_metrics['average_approval_time'] = float(row.avg_days or 0)
            elif 'Access Count' in metric_name:
                document_metrics['total_access_count'] = int(row.total_count or 0)
            elif 'Revision Rate' in metric_name:
                document_metrics['revision_rate'] = float(row.avg_percentage or 0)
                
            document_metrics['metrics_detail'][metric_name] = {
                'subcategory': row.metric_subcategory,
                'total_count': int(row.total_count or 0),
                'average_days': float(row.avg_days or 0),
                'average_percentage': float(row.avg_percentage or 0),
                'measurement_count': row.measurement_count
            }
            
        return document_metrics
    
    def collect_organizational_metrics(self, department_id: Optional[int] = None,
                                     period_days: int = 30) -> Dict[str, Any]:
        """
        Collect organizational and departmental metrics.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Organizational metrics query
        query = self.db.execute(text("""
            SELECT 
                metric_name,
                metric_subcategory,
                department_id,
                AVG(value) as avg_value,
                MAX(value) as max_value,
                COUNT(*) as measurement_count,
                MAX(measurement_date) as latest_measurement
            FROM analytics_metrics 
            WHERE metric_category = 'organizational'
            AND is_deleted = FALSE
            AND measurement_date >= :start_date
            AND measurement_date <= :end_date
            {dept_filter}
            GROUP BY metric_name, metric_subcategory, department_id
        """.format(
            dept_filter="AND department_id = :dept_id" if department_id else ""
        )), {
            'start_date': start_date,
            'end_date': end_date,
            'dept_id': department_id
        })
        
        results = query.fetchall()
        
        org_metrics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'department_id': department_id,
            'active_users': 0,
            'department_efficiency': 0,
            'collaboration_score': 0,
            'department_breakdown': {},
            'metrics_detail': {}
        }
        
        for row in results:
            metric_name = row.metric_name
            dept_id = row.department_id
            
            if 'Active Users' in metric_name:
                org_metrics['active_users'] = int(row.max_value or 0)
            elif 'Efficiency Score' in metric_name:
                if dept_id == department_id or department_id is None:
                    org_metrics['department_efficiency'] = float(row.avg_value or 0)
            elif 'Collaboration' in metric_name:
                org_metrics['collaboration_score'] = float(row.avg_value or 0)
                
            # Department breakdown
            if dept_id and dept_id not in org_metrics['department_breakdown']:
                org_metrics['department_breakdown'][dept_id] = {}
                
            if dept_id:
                org_metrics['department_breakdown'][dept_id][metric_name] = {
                    'average': float(row.avg_value or 0),
                    'maximum': float(row.max_value or 0),
                    'measurement_count': row.measurement_count,
                    'latest_measurement': row.latest_measurement.isoformat() if row.latest_measurement else None
                }
                
        return org_metrics
    
    # ========================================
    # KPI DASHBOARD METHODS
    # ========================================
    
    def generate_kpi_dashboard_data(self, user_permissions: List[str],
                                  department_id: Optional[int] = None,
                                  period_days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive KPI dashboard data based on user permissions.
        """
        dashboard_data = {
            'period': period_days,
            'department_id': department_id,
            'generated_at': datetime.utcnow().isoformat(),
            'user_permissions': user_permissions,
            'sections': {}
        }
        
        # Quality section (if user has quality permissions)
        if any(perm in user_permissions for perm in ['quality.view', 'quality.manage', 'admin']):
            dashboard_data['sections']['quality'] = self.collect_quality_metrics(department_id, period_days)
            
        # Training section (if user has training permissions)
        if any(perm in user_permissions for perm in ['training.view', 'training.manage', 'admin']):
            dashboard_data['sections']['training'] = self.collect_training_metrics(department_id, period_days)
            
        # Documents section (if user has document permissions)
        if any(perm in user_permissions for perm in ['documents.view', 'documents.manage', 'admin']):
            dashboard_data['sections']['documents'] = self.collect_document_metrics(department_id, period_days)
            
        # Organizational section (if user has organizational permissions)
        if any(perm in user_permissions for perm in ['organization.view', 'admin']):
            dashboard_data['sections']['organizational'] = self.collect_organizational_metrics(department_id, period_days)
            
        return dashboard_data
    
    # ========================================
    # METRICS STORAGE METHODS
    # ========================================
    
    def store_metric(self, metric_name: str, metric_category: str, value: Union[float, int, str],
                    unit: str, department_id: Optional[int] = None, 
                    entity_type: Optional[str] = None, entity_id: Optional[int] = None,
                    **kwargs) -> bool:
        """
        Store a new metric in the analytics_metrics table.
        """
        try:
            # Prepare metric data
            metric_data = {
                'metric_name': metric_name,
                'metric_category': metric_category,
                'metric_subcategory': kwargs.get('subcategory'),
                'unit': unit,
                'department_id': department_id,
                'user_id': kwargs.get('user_id'),
                'organization_id': kwargs.get('organization_id'),
                'module_name': kwargs.get('module_name'),
                'entity_type': entity_type,
                'entity_id': entity_id,
                'period_start': kwargs.get('period_start'),
                'period_end': kwargs.get('period_end'),
                'calculation_method': kwargs.get('calculation_method'),
                'data_source': kwargs.get('data_source'),
                'confidence_level': kwargs.get('confidence_level', 100.0),
                'tags': json.dumps(kwargs.get('tags', {})),
                'created_by': self.current_user.id
            }
            
            # Handle different value types
            if isinstance(value, (int, float)):
                metric_data['value'] = Decimal(str(value))
            else:
                metric_data['value_text'] = str(value)
                
            # Insert into database
            insert_query = text("""
                INSERT INTO analytics_metrics (
                    metric_name, metric_category, metric_subcategory, value, value_text,
                    unit, department_id, user_id, organization_id, module_name,
                    entity_type, entity_id, period_start, period_end,
                    calculation_method, data_source, confidence_level, tags, created_by
                ) VALUES (
                    :metric_name, :metric_category, :metric_subcategory, :value, :value_text,
                    :unit, :department_id, :user_id, :organization_id, :module_name,
                    :entity_type, :entity_id, :period_start, :period_end,
                    :calculation_method, :data_source, :confidence_level, :tags, :created_by
                )
            """)
            
            self.db.execute(insert_query, metric_data)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error storing metric: {e}")
            return False
    
    # ========================================
    # CACHE MANAGEMENT METHODS
    # ========================================
    
    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analytics data if it exists and hasn't expired.
        """
        query = self.db.execute(text("""
            SELECT data, hit_count, expires_at
            FROM analytics_cache 
            WHERE cache_key = :cache_key 
            AND expires_at > NOW()
        """), {'cache_key': cache_key})
        
        result = query.fetchone()
        
        if result:
            # Update hit count
            self.db.execute(text("""
                UPDATE analytics_cache 
                SET hit_count = hit_count + 1, last_hit = NOW()
                WHERE cache_key = :cache_key
            """), {'cache_key': cache_key})
            self.db.commit()
            
            return json.loads(result.data)
            
        return None
    
    def cache_data(self, cache_key: str, data: Dict[str, Any], 
                  category: str = 'dashboard', expire_hours: int = 1) -> bool:
        """
        Cache analytics data with expiration.
        """
        try:
            expires_at = datetime.utcnow() + timedelta(hours=expire_hours)
            data_json = json.dumps(data, default=str)
            data_hash = hashlib.md5(data_json.encode()).hexdigest()
            
            # Upsert cache entry
            self.db.execute(text("""
                INSERT INTO analytics_cache (
                    cache_key, cache_category, data, data_hash, expires_at
                ) VALUES (
                    :cache_key, :category, :data, :data_hash, :expires_at
                ) ON CONFLICT (cache_key) DO UPDATE SET
                    data = EXCLUDED.data,
                    data_hash = EXCLUDED.data_hash,
                    expires_at = EXCLUDED.expires_at,
                    hit_count = 0,
                    created_at = NOW()
            """), {
                'cache_key': cache_key,
                'category': category,
                'data': data_json,
                'data_hash': data_hash,
                'expires_at': expires_at
            })
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error caching data: {e}")
            return False
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries and return count of removed entries.
        """
        result = self.db.execute(text("""
            DELETE FROM analytics_cache 
            WHERE expires_at < NOW()
        """))
        
        deleted_count = result.rowcount
        self.db.commit()
        
        return deleted_count


# Factory function
def create_analytics_service(db: Session, current_user: Optional[User] = None) -> AnalyticsService:
    """Create and configure analytics service"""
    if current_user is None:
        # Create a mock user for system operations
        from unittest.mock import Mock
        current_user = Mock()
        current_user.id = 1
    return AnalyticsService(db=db, current_user=current_user)