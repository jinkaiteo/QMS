# Data Aggregation Service - Phase B Sprint 2 Day 2
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
import json
import hashlib
import logging
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Configuration for a data source"""
    name: str
    endpoint: str
    method: str = 'GET'
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    cache_ttl: int = 300  # 5 minutes default
    retry_count: int = 3
    required: bool = True
    transform_function: Optional[str] = None

@dataclass
class AggregationResult:
    """Result of data aggregation operation"""
    success: bool
    data: Dict[str, Any]
    sources_collected: List[str]
    sources_failed: List[str]
    collection_time_ms: int
    cache_hits: int
    cache_misses: int
    errors: List[str]

class DataAggregationService:
    """
    Advanced data aggregation service for report generation
    Collects data from multiple sources with caching and error handling
    """
    
    def __init__(self, db: Session, cache_service=None):
        self.db = db
        self.cache_service = cache_service
        self.base_url = "http://localhost:8000"  # API backend
        
    async def aggregate_report_data(self, 
                                   data_sources: List[DataSource], 
                                   parameters: Dict[str, Any],
                                   template_id: Optional[int] = None) -> AggregationResult:
        """
        Aggregate data from multiple sources for report generation
        
        Args:
            data_sources: List of data source configurations
            parameters: Report parameters for filtering and customization
            template_id: Template ID for cache optimization
            
        Returns:
            AggregationResult with collected data and metadata
        """
        start_time = datetime.now()
        collected_data = {}
        sources_collected = []
        sources_failed = []
        errors = []
        cache_hits = 0
        cache_misses = 0
        
        try:
            logger.info(f"Starting data aggregation for {len(data_sources)} sources")
            
            # Process data sources concurrently
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                tasks = []
                
                for source in data_sources:
                    task = self._collect_from_source(
                        session, source, parameters, template_id
                    )
                    tasks.append((source.name, task))
                
                # Wait for all tasks to complete
                for source_name, task in tasks:
                    try:
                        source_data, was_cached = await task
                        collected_data[source_name] = source_data
                        sources_collected.append(source_name)
                        
                        if was_cached:
                            cache_hits += 1
                        else:
                            cache_misses += 1
                            
                        logger.debug(f"Collected data from source: {source_name}")
                            
                    except Exception as e:
                        source = next(s for s in data_sources if s.name == source_name)
                        error_msg = f"Source '{source_name}' failed: {str(e)}"
                        
                        if source.required:
                            errors.append(f"Required {error_msg}")
                            logger.error(f"Required {error_msg}")
                        else:
                            logger.warning(f"Optional {error_msg}")
                            
                        sources_failed.append(source_name)
            
            # Post-process collected data
            processed_data = await self._post_process_data(collected_data, parameters)
            
            # Calculate collection time
            collection_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"Data aggregation completed in {collection_time}ms")
            
            return AggregationResult(
                success=len(errors) == 0,
                data=processed_data,
                sources_collected=sources_collected,
                sources_failed=sources_failed,
                collection_time_ms=collection_time,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                errors=errors
            )
            
        except Exception as e:
            collection_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Data aggregation failed: {str(e)}")
            
            return AggregationResult(
                success=False,
                data={},
                sources_collected=sources_collected,
                sources_failed=sources_failed,
                collection_time_ms=collection_time,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                errors=[f"Aggregation failed: {str(e)}"]
            )
    
    async def _collect_from_source(self, 
                                  session: aiohttp.ClientSession,
                                  source: DataSource, 
                                  parameters: Dict[str, Any],
                                  template_id: Optional[int] = None) -> tuple[Dict[str, Any], bool]:
        """Collect data from a single source with caching"""
        
        # Generate cache key
        cache_key = self._generate_cache_key(source, parameters, template_id)
        
        # Check cache first
        if self.cache_service:
            cached_data = await self.cache_service.get_async(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for source: {source.name}")
                return cached_data, True
        
        # Collect fresh data
        data = await self._fetch_source_data(session, source, parameters)
        
        # Cache the result
        if self.cache_service and data:
            await self.cache_service.set_async(cache_key, data, ttl=source.cache_ttl)
            
        return data, False
    
    async def _fetch_source_data(self, 
                                session: aiohttp.ClientSession,
                                source: DataSource, 
                                parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from source with retry logic"""
        
        for attempt in range(source.retry_count):
            try:
                if source.endpoint.startswith('/api/'):
                    # Internal API call
                    return await self._fetch_internal_api(source, parameters)
                elif source.endpoint.startswith('db:'):
                    # Direct database query
                    return await self._fetch_database_query(source, parameters)
                else:
                    # External HTTP call
                    return await self._fetch_external_api(session, source, parameters)
                    
            except Exception as e:
                if attempt == source.retry_count - 1:
                    raise e
                    
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed for {source.name}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
        
        return {}
    
    async def _fetch_internal_api(self, source: DataSource, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from internal API endpoints"""
        
        # Map common endpoints to service methods
        endpoint_map = {
            '/api/v1/analytics/training': self._get_training_analytics,
            '/api/v1/analytics/quality': self._get_quality_analytics,
            '/api/v1/analytics/documents': self._get_document_analytics,
            '/api/v1/analytics/users': self._get_user_analytics,
            '/api/v1/analytics/departments': self._get_department_analytics,
        }
        
        if source.endpoint in endpoint_map:
            return await endpoint_map[source.endpoint](parameters)
        else:
            # Generic API call
            url = f"{self.base_url}{source.endpoint}"
            async with aiohttp.ClientSession() as session:
                return await self._fetch_external_api(session, source, parameters)
    
    async def _fetch_database_query(self, source: DataSource, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute direct database queries"""
        
        query_name = source.endpoint.replace('db:', '')
        
        # Predefined safe queries
        queries = {
            'training_completion_rates': """
                SELECT 
                    tp.title as program_name,
                    COUNT(ta.id) as total_assignments,
                    COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) as completed,
                    ROUND(
                        COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(ta.id), 0), 2
                    ) as completion_rate
                FROM training_programs tp
                LEFT JOIN training_assignments ta ON tp.id = ta.program_id
                WHERE tp.is_deleted = false
                AND (ta.created_at >= :start_date OR :start_date IS NULL)
                AND (ta.created_at <= :end_date OR :end_date IS NULL)
                GROUP BY tp.id, tp.title
                ORDER BY completion_rate DESC
            """,
            
            'quality_events_summary': """
                SELECT 
                    event_type,
                    status,
                    COUNT(*) as count,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/86400) as avg_resolution_days
                FROM quality_events
                WHERE is_deleted = false
                AND (created_at >= :start_date OR :start_date IS NULL)
                AND (created_at <= :end_date OR :end_date IS NULL)
                GROUP BY event_type, status
                ORDER BY event_type, status
            """,
            
            'document_statistics': """
                SELECT 
                    category,
                    status,
                    COUNT(*) as count,
                    AVG(version) as avg_version
                FROM documents
                WHERE is_deleted = false
                AND (created_at >= :start_date OR :start_date IS NULL)
                AND (created_at <= :end_date OR :end_date IS NULL)
                GROUP BY category, status
                ORDER BY category, status
            """,
            
            'user_activity_summary': """
                SELECT 
                    u.department,
                    COUNT(u.id) as total_users,
                    COUNT(CASE WHEN u.is_active = true THEN 1 END) as active_users,
                    COUNT(CASE WHEN u.last_login >= NOW() - INTERVAL '30 days' THEN 1 END) as recent_logins
                FROM users u
                WHERE u.is_deleted = false
                GROUP BY u.department
                ORDER BY u.department
            """
        }
        
        if query_name not in queries:
            raise ValueError(f"Unknown database query: {query_name}")
        
        try:
            # Execute query with parameters
            result = self.db.execute(text(queries[query_name]), parameters)
            
            # Convert to list of dictionaries
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result.fetchall()]
            
            return {'data': data, 'total': len(data)}
            
        except Exception as e:
            logger.error(f"Database query failed for {query_name}: {str(e)}")
            raise e
    
    async def _fetch_external_api(self, 
                                 session: aiohttp.ClientSession,
                                 source: DataSource, 
                                 parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from external HTTP endpoints"""
        
        url = source.endpoint if source.endpoint.startswith('http') else f"{self.base_url}{source.endpoint}"
        headers = source.headers or {}
        params = {**(source.params or {}), **parameters}
        
        async with session.request(
            source.method,
            url,
            headers=headers,
            params=params if source.method == 'GET' else None,
            json=params if source.method != 'GET' else None,
            timeout=source.timeout
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def _get_training_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get training analytics data"""
        
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        # Training completion rates
        completion_query = """
            SELECT 
                tp.title as program_name,
                tp.description,
                COUNT(ta.id) as total_assignments,
                COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN ta.status = 'in_progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN ta.status = 'not_started' THEN 1 END) as not_started,
                ROUND(
                    COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(ta.id), 0), 2
                ) as completion_rate
            FROM training_programs tp
            LEFT JOIN training_assignments ta ON tp.id = ta.program_id
            WHERE tp.is_deleted = false
            AND (:start_date IS NULL OR ta.created_at >= :start_date)
            AND (:end_date IS NULL OR ta.created_at <= :end_date)
            GROUP BY tp.id, tp.title, tp.description
            ORDER BY completion_rate DESC
        """
        
        result = self.db.execute(text(completion_query), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        programs = [dict(zip(result.keys(), row)) for row in result.fetchall()]
        
        return {
            'programs': programs,
            'summary': {
                'total_programs': len(programs),
                'avg_completion_rate': sum(p['completion_rate'] or 0 for p in programs) / len(programs) if programs else 0
            }
        }
    
    async def _get_quality_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get quality events analytics"""
        
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        events_query = """
            SELECT 
                event_type,
                status,
                priority,
                COUNT(*) as count,
                AVG(EXTRACT(EPOCH FROM (COALESCE(resolved_at, NOW()) - created_at))/86400) as avg_resolution_days
            FROM quality_events
            WHERE is_deleted = false
            AND (:start_date IS NULL OR created_at >= :start_date)
            AND (:end_date IS NULL OR created_at <= :end_date)
            GROUP BY event_type, status, priority
            ORDER BY event_type, status, priority
        """
        
        result = self.db.execute(text(events_query), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        events = [dict(zip(result.keys(), row)) for row in result.fetchall()]
        
        return {
            'events': events,
            'summary': {
                'total_events': sum(e['count'] for e in events),
                'avg_resolution_time': sum(e['avg_resolution_days'] or 0 for e in events) / len(events) if events else 0
            }
        }
    
    async def _get_document_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get document analytics"""
        
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        docs_query = """
            SELECT 
                category,
                status,
                COUNT(*) as count,
                AVG(version) as avg_version,
                MAX(version) as max_version
            FROM documents
            WHERE is_deleted = false
            AND (:start_date IS NULL OR created_at >= :start_date)
            AND (:end_date IS NULL OR created_at <= :end_date)
            GROUP BY category, status
            ORDER BY category, status
        """
        
        result = self.db.execute(text(docs_query), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        documents = [dict(zip(result.keys(), row)) for row in result.fetchall()]
        
        return {
            'documents': documents,
            'summary': {
                'total_documents': sum(d['count'] for d in documents),
                'categories': len(set(d['category'] for d in documents))
            }
        }
    
    async def _get_user_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user analytics"""
        
        users_query = """
            SELECT 
                department,
                role,
                COUNT(*) as count,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
                COUNT(CASE WHEN last_login >= NOW() - INTERVAL '30 days' THEN 1 END) as recent_logins
            FROM users
            WHERE is_deleted = false
            GROUP BY department, role
            ORDER BY department, role
        """
        
        result = self.db.execute(text(users_query))
        users = [dict(zip(result.keys(), row)) for row in result.fetchall()]
        
        return {
            'users': users,
            'summary': {
                'total_users': sum(u['count'] for u in users),
                'active_users': sum(u['active_count'] for u in users),
                'departments': len(set(u['department'] for u in users))
            }
        }
    
    async def _get_department_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get department analytics"""
        
        dept_query = """
            SELECT 
                d.name as department_name,
                d.code as department_code,
                COUNT(u.id) as user_count,
                COUNT(ta.id) as training_assignments,
                COUNT(qe.id) as quality_events
            FROM departments d
            LEFT JOIN users u ON d.name = u.department AND u.is_deleted = false
            LEFT JOIN training_assignments ta ON u.id = ta.user_id AND ta.is_deleted = false
            LEFT JOIN quality_events qe ON u.id = qe.reporter_id AND qe.is_deleted = false
            WHERE d.is_deleted = false
            GROUP BY d.id, d.name, d.code
            ORDER BY d.name
        """
        
        result = self.db.execute(text(dept_query))
        departments = [dict(zip(result.keys(), row)) for row in result.fetchall()]
        
        return {
            'departments': departments,
            'summary': {
                'total_departments': len(departments),
                'total_users': sum(d['user_count'] for d in departments)
            }
        }
    
    async def _post_process_data(self, collected_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process and combine collected data"""
        
        processed = {
            'raw_data': collected_data,
            'metadata': {
                'collection_timestamp': datetime.now().isoformat(),
                'parameters': parameters,
                'sources_count': len(collected_data)
            }
        }
        
        # Add computed metrics
        if 'training_analytics' in collected_data and 'user_analytics' in collected_data:
            training_data = collected_data['training_analytics']
            user_data = collected_data['user_analytics']
            
            # Calculate training penetration rate
            total_users = user_data.get('summary', {}).get('active_users', 0)
            total_assignments = sum(p.get('total_assignments', 0) for p in training_data.get('programs', []))
            
            processed['computed_metrics'] = {
                'training_penetration_rate': round(total_assignments / max(total_users, 1) * 100, 2),
                'avg_assignments_per_user': round(total_assignments / max(total_users, 1), 2)
            }
        
        return processed
    
    def _generate_cache_key(self, source: DataSource, parameters: Dict[str, Any], template_id: Optional[int] = None) -> str:
        """Generate cache key for data source"""
        
        key_data = {
            'source': source.name,
            'endpoint': source.endpoint,
            'parameters': sorted(parameters.items()),
            'template_id': template_id
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return f"data_agg:{hashlib.md5(key_string.encode()).hexdigest()}"

# Factory function for easy service creation
def create_data_aggregator(db: Session, cache_service=None) -> DataAggregationService:
    """Create and configure data aggregation service"""
    return DataAggregationService(db=db, cache_service=cache_service)