# QMS Analytics API Endpoints - Phase B Sprint 2 Day 2 Enhanced
# Includes Template Processing Pipeline endpoints
# FastAPI endpoints for analytics data, dashboards, and metrics

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.analytics.analytics_service import AnalyticsService
from pydantic import BaseModel

router = APIRouter()

# ========================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE
# ========================================

class MetricRequest(BaseModel):
    metric_name: str
    metric_category: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: str
    department_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    subcategory: Optional[str] = None
    module_name: Optional[str] = None
    calculation_method: Optional[str] = None
    data_source: Optional[str] = None
    confidence_level: Optional[float] = 100.0
    tags: Optional[Dict[str, Any]] = {}

class DashboardResponse(BaseModel):
    period: int
    department_id: Optional[int]
    generated_at: str
    sections: Dict[str, Any]

class MetricsResponse(BaseModel):
    period: Dict[str, Any]
    department_id: Optional[int]
    metrics: Dict[str, Any]
    summary: Dict[str, Any]

# ========================================
# DASHBOARD ENDPOINTS
# ========================================

@router.get("/dashboards/overview", response_model=DashboardResponse)
async def get_overview_dashboard(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive overview dashboard data for executives and managers.
    
    Includes:
    - Quality metrics summary
    - Training compliance status  
    - Document usage statistics
    - Organizational performance indicators
    
    Permissions required:
    - dashboard.view: Can view dashboard data
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        
        # Get user permissions (simplified for now)
        user_permissions = ['quality.view', 'training.view', 'documents.view', 'organization.view']
        
        # Check cache first
        cache_key = f"dashboard_overview_{department_id}_{period_days}_{current_user.id}"
        cached_data = analytics_service.get_cached_data(cache_key)
        
        if cached_data:
            return DashboardResponse(**cached_data)
        
        # Generate fresh dashboard data
        dashboard_data = analytics_service.generate_kpi_dashboard_data(
            user_permissions=user_permissions,
            department_id=department_id,
            period_days=period_days
        )
        
        # Cache the results for 15 minutes
        analytics_service.cache_data(cache_key, dashboard_data, expire_hours=0.25)
        
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")

@router.get("/dashboards/quality", response_model=MetricsResponse)
async def get_quality_dashboard(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quality-focused dashboard data with detailed quality metrics.
    
    Includes:
    - Quality event statistics
    - CAPA effectiveness rates
    - Resolution time metrics
    - Compliance scores
    
    Permissions required:
    - quality.view: Can view quality metrics
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        
        # Check cache
        cache_key = f"dashboard_quality_{department_id}_{period_days}"
        cached_data = analytics_service.get_cached_data(cache_key)
        
        if cached_data:
            return MetricsResponse(**cached_data)
        
        # Generate quality metrics
        quality_data = analytics_service.collect_quality_metrics(
            department_id=department_id,
            period_days=period_days
        )
        
        # Cache for 10 minutes
        analytics_service.cache_data(cache_key, quality_data, expire_hours=0.167)
        
        return MetricsResponse(**quality_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quality metrics: {str(e)}")

@router.get("/dashboards/training", response_model=Dict[str, Any])
async def get_training_dashboard(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get training-focused dashboard data with completion rates and compliance.
    
    Includes:
    - Training completion rates
    - Overdue training counts
    - Average training scores
    - Hours completed statistics
    
    Permissions required:
    - training.view: Can view training metrics
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        
        # Check cache
        cache_key = f"dashboard_training_{department_id}_{period_days}"
        cached_data = analytics_service.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # Generate training metrics
        training_data = analytics_service.collect_training_metrics(
            department_id=department_id,
            period_days=period_days
        )
        
        # Cache for 20 minutes
        analytics_service.cache_data(cache_key, training_data, expire_hours=0.333)
        
        return training_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching training metrics: {str(e)}")

@router.get("/dashboards/documents", response_model=Dict[str, Any])
async def get_documents_dashboard(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get document-focused dashboard data with usage and workflow metrics.
    
    Includes:
    - Document creation statistics
    - Approval workflow performance
    - Document access patterns
    - Revision rates
    
    Permissions required:
    - documents.view: Can view document metrics
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        
        # Check cache
        cache_key = f"dashboard_documents_{department_id}_{period_days}"
        cached_data = analytics_service.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # Generate document metrics
        document_data = analytics_service.collect_document_metrics(
            department_id=department_id,
            period_days=period_days
        )
        
        # Cache for 30 minutes
        analytics_service.cache_data(cache_key, document_data, expire_hours=0.5)
        
        return document_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document metrics: {str(e)}")

# ========================================
# METRICS COLLECTION ENDPOINTS
# ========================================

@router.post("/metrics")
async def store_metric(
    metric: MetricRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store a new metric in the analytics system.
    
    Used by other QMS modules to record metrics for analytics.
    
    Permissions required:
    - metrics.create: Can create new metrics
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        
        # Prepare additional parameters
        kwargs = {
            'subcategory': metric.subcategory,
            'module_name': metric.module_name,
            'calculation_method': metric.calculation_method,
            'data_source': metric.data_source,
            'confidence_level': metric.confidence_level,
            'tags': metric.tags
        }
        
        # Store the metric
        success = analytics_service.store_metric(
            metric_name=metric.metric_name,
            metric_category=metric.metric_category,
            value=metric.value if metric.value is not None else metric.value_text,
            unit=metric.unit,
            department_id=metric.department_id,
            entity_type=metric.entity_type,
            entity_id=metric.entity_id,
            **kwargs
        )
        
        if success:
            return {"message": "Metric stored successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to store metric")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing metric: {str(e)}")

@router.get("/metrics/{category}")
async def get_metrics_by_category(
    category: str = Path(..., description="Metric category"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    metric_name: Optional[str] = Query(None, description="Filter by specific metric name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get metrics by category with optional filtering.
    
    Categories: quality, training, documents, organizational, compliance
    
    Permissions required:
    - metrics.view: Can view metrics data
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        
        # Route to appropriate collection method based on category
        if category == 'quality':
            return analytics_service.collect_quality_metrics(department_id, period_days)
        elif category == 'training':
            return analytics_service.collect_training_metrics(department_id, period_days)
        elif category == 'documents':
            return analytics_service.collect_document_metrics(department_id, period_days)
        elif category == 'organizational':
            return analytics_service.collect_organizational_metrics(department_id, period_days)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")

# ========================================
# UTILITY ENDPOINTS
# ========================================

@router.get("/health")
async def analytics_health_check():
    """
    Health check endpoint for analytics service.
    """
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.delete("/cache/cleanup")
async def cleanup_expired_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clean up expired cache entries.
    
    Permissions required:
    - admin: Can perform cache cleanup
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        deleted_count = analytics_service.cleanup_expired_cache()
        
        return {
            "message": f"Cleaned up {deleted_count} expired cache entries",
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning cache: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics cache statistics.
    
    Permissions required:
    - admin: Can view cache statistics
    """
    try:
        from sqlalchemy import text
        
        # Get cache statistics
        stats_query = db.execute(text("""
            SELECT 
                cache_category,
                COUNT(*) as entry_count,
                AVG(hit_count) as avg_hit_count,
                MAX(hit_count) as max_hit_count,
                COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active_entries,
                COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_entries
            FROM analytics_cache
            GROUP BY cache_category
        """))
        
        stats = []
        for row in stats_query:
            stats.append({
                'category': row.cache_category,
                'total_entries': row.entry_count,
                'active_entries': row.active_entries,
                'expired_entries': row.expired_entries,
                'average_hit_count': float(row.avg_hit_count or 0),
                'max_hit_count': row.max_hit_count
            })
        
        return {
            "cache_statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cache stats: {str(e)}")

# ========================================
# DEPARTMENT ANALYTICS ENDPOINTS
# ========================================

@router.get("/departments/{department_id}/analytics")
async def get_department_analytics(
    department_id: int = Path(..., description="Department ID"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    include_children: bool = Query(False, description="Include child departments"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for a specific department.
    
    Includes all metric categories for the department and optionally
    its child departments in the hierarchy.
    
    Permissions required:
    - department.view: Can view department analytics
    """
    try:
        analytics_service = AnalyticsService(db, current_user)
        
        # Check cache
        cache_key = f"dept_analytics_{department_id}_{period_days}_{include_children}"
        cached_data = analytics_service.get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # Collect all metrics for the department
        user_permissions = ['quality.view', 'training.view', 'documents.view', 'organization.view']
        
        department_analytics = analytics_service.generate_kpi_dashboard_data(
            user_permissions=user_permissions,
            department_id=department_id,
            period_days=period_days
        )
        
        # Add department-specific metadata
        department_analytics['include_children'] = include_children
        department_analytics['department_focus'] = True
        
        # Cache for 20 minutes
        analytics_service.cache_data(cache_key, department_analytics, expire_hours=0.333)
        
        return department_analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching department analytics: {str(e)}")

@router.get("/trends/{metric_name}")
async def get_metric_trends(
    metric_name: str = Path(..., description="Metric name"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    period_days: int = Query(90, ge=7, le=365, description="Analysis period in days"),
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get trend data for a specific metric over time.
    
    Returns time-series data suitable for trend charts and analysis.
    
    Permissions required:
    - trends.view: Can view trend analysis
    """
    try:
        from sqlalchemy import text
        
        # Build trend query based on granularity
        if granularity == "daily":
            date_trunc = "DATE_TRUNC('day', measurement_date)"
        elif granularity == "weekly":
            date_trunc = "DATE_TRUNC('week', measurement_date)"
        else:  # monthly
            date_trunc = "DATE_TRUNC('month', measurement_date)"
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        query_sql = f"""
            SELECT 
                {date_trunc} as period,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                COUNT(*) as measurement_count
            FROM analytics_metrics 
            WHERE metric_name = :metric_name
            AND is_deleted = FALSE
            AND measurement_date >= :start_date
            AND measurement_date <= :end_date
            {' AND department_id = :dept_id' if department_id else ''}
            GROUP BY {date_trunc}
            ORDER BY period ASC
        """
        
        params = {
            'metric_name': metric_name,
            'start_date': start_date,
            'end_date': end_date
        }
        
        if department_id:
            params['dept_id'] = department_id
        
        result = db.execute(text(query_sql), params)
        
        trend_data = []
        for row in result:
            trend_data.append({
                'period': row.period.isoformat() if row.period else None,
                'average_value': float(row.avg_value) if row.avg_value else 0,
                'minimum_value': float(row.min_value) if row.min_value else 0,
                'maximum_value': float(row.max_value) if row.max_value else 0,
                'measurement_count': row.measurement_count
            })
        
        return {
            'metric_name': metric_name,
            'department_id': department_id,
            'period_days': period_days,
            'granularity': granularity,
            'data_points': len(trend_data),
            'trend_data': trend_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trend data: {str(e)}")


# ========================================
# TEMPLATE PROCESSING PIPELINE ENDPOINTS
# Phase B Sprint 2 Day 2 - Template Processing
# ========================================

from app.services.reporting.template_processing_service import (
    TemplateProcessingService, 
    TemplateProcessingRequest, 
    create_template_processing_service
)
from app.services.reporting.data_aggregator import create_data_aggregator
from app.services.reporting.template_validator import create_template_validator
from app.services.reporting.enhanced_chart_service import create_enhanced_chart_service
from app.services.reporting.cache_service import get_cache_service
from app.services.reporting.processing_orchestrator import (
    ReportProcessingOrchestrator,
    ProcessingPriority,
    create_processing_orchestrator
)

class TemplateProcessingRequestModel(BaseModel):
    """Request model for template processing"""
    template_id: int
    parameters: Dict[str, Any]
    output_format: str = 'both'  # 'pdf', 'excel', 'both'
    validate_template: bool = True
    generate_charts: bool = True
    cache_results: bool = True
    priority: str = 'normal'  # 'low', 'normal', 'high', 'urgent'

class DataAggregationRequestModel(BaseModel):
    """Request model for data aggregation testing"""
    data_sources: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    template_id: Optional[int] = None

class ChartGenerationRequestModel(BaseModel):
    """Request model for chart generation testing"""
    chart_type: str
    chart_data: Dict[str, Any]
    chart_config: Dict[str, Any]
    output_format: str = 'both'

@router.post("/templates/{template_id}/process")
async def process_template(
    template_id: int,
    request: TemplateProcessingRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a complete template through the Template Processing Pipeline
    Includes validation, data aggregation, chart generation, and report creation
    """
    try:
        # Create processing service
        cache_service = get_cache_service()
        processing_service = create_template_processing_service(
            db=db,
            cache_service=cache_service
        )
        
        # Create processing request
        processing_request = TemplateProcessingRequest(
            template_id=template_id,
            parameters=request.parameters,
            output_format=request.output_format,
            validate_template=request.validate_template,
            generate_charts=request.generate_charts,
            cache_results=request.cache_results,
            priority=request.priority
        )
        
        # Process template
        result = await processing_service.process_template(processing_request)
        
        # Convert result to JSON-serializable format
        response = {
            'success': result.success,
            'template_id': result.template_id,
            'processing_id': result.processing_id,
            'generated_files': result.generated_files,
            'processing_time_ms': result.processing_time_ms,
            'error_message': result.error_message,
            'metadata': result.metadata
        }
        
        # Add validation results if available
        if result.validation_result:
            response['validation'] = {
                'is_valid': result.validation_result.is_valid,
                'error_count': result.validation_result.error_count,
                'warning_count': result.validation_result.warning_count
            }
        
        # Add aggregation metrics if available
        if result.aggregation_result:
            response['data_aggregation'] = {
                'success': result.aggregation_result.success,
                'sources_collected': len(result.aggregation_result.sources_collected),
                'sources_failed': len(result.aggregation_result.sources_failed),
                'collection_time_ms': result.aggregation_result.collection_time_ms,
                'cache_hits': result.aggregation_result.cache_hits,
                'cache_misses': result.aggregation_result.cache_misses
            }
        
        # Add chart results if available
        if result.chart_results:
            response['charts'] = {
                'total_charts': len(result.chart_results),
                'successful_charts': len([r for r in result.chart_results if r.success]),
                'failed_charts': len([r for r in result.chart_results if not r.success])
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template processing failed: {str(e)}")

@router.post("/data-aggregation/test")
async def test_data_aggregation(
    request: DataAggregationRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test data aggregation functionality
    Useful for testing data sources and configurations
    """
    try:
        # Create data aggregator
        cache_service = get_cache_service()
        data_aggregator = create_data_aggregator(db=db, cache_service=cache_service)
        
        # Convert request data sources to DataSource objects
        from app.services.reporting.data_aggregator import DataSource
        
        data_sources = []
        for source_config in request.data_sources:
            data_source = DataSource(
                name=source_config['name'],
                endpoint=source_config['endpoint'],
                method=source_config.get('method', 'GET'),
                headers=source_config.get('headers', {}),
                params=source_config.get('params', {}),
                timeout=source_config.get('timeout', 30),
                cache_ttl=source_config.get('cache_ttl', 300),
                retry_count=source_config.get('retry_count', 3),
                required=source_config.get('required', True)
            )
            data_sources.append(data_source)
        
        # Aggregate data
        result = await data_aggregator.aggregate_report_data(
            data_sources, request.parameters, request.template_id
        )
        
        # Return results
        return {
            'success': result.success,
            'sources_collected': result.sources_collected,
            'sources_failed': result.sources_failed,
            'collection_time_ms': result.collection_time_ms,
            'cache_hits': result.cache_hits,
            'cache_misses': result.cache_misses,
            'errors': result.errors,
            'data_summary': {
                'raw_sources': len(result.data.get('raw_data', {})),
                'metadata_keys': list(result.data.get('metadata', {}).keys()) if result.data.get('metadata') else []
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data aggregation test failed: {str(e)}")

@router.post("/charts/generate")
async def generate_chart(
    request: ChartGenerationRequestModel,
    current_user: User = Depends(get_current_user)
):
    """
    Generate charts using the Enhanced Chart Service
    Useful for testing chart configurations
    """
    try:
        # Create chart service
        cache_service = get_cache_service()
        chart_service = create_enhanced_chart_service(cache_service=cache_service)
        
        # Generate chart
        result = await chart_service.generate_chart(
            chart_type=request.chart_type,
            chart_data=request.chart_data,
            chart_config=request.chart_config,
            output_format=request.output_format
        )
        
        # Return result
        response = {
            'success': result.success,
            'chart_id': result.chart_id,
            'chart_type': result.chart_type,
            'format': result.format,
            'generation_time_ms': result.generation_time_ms,
            'error_message': result.error_message,
            'metadata': result.metadata
        }
        
        # Add format-specific results
        if result.pdf_drawing:
            response['pdf_available'] = True
        if result.excel_chart_ref:
            response['excel_available'] = True
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")

@router.get("/templates/{template_id}/validate")
async def validate_template(
    template_id: int,
    run_tests: bool = Query(False, description="Run performance and data quality tests"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate a template configuration
    Checks template structure, data sources, charts, and parameters
    """
    try:
        # Create template validator
        data_aggregator = create_data_aggregator(db=db)
        template_validator = create_template_validator(db=db, data_aggregator=data_aggregator)
        
        # Validate template
        validation_result = template_validator.validate_template(template_id, run_tests=run_tests)
        
        # Generate validation report
        validation_report = template_validator.generate_validation_report(validation_result)
        
        return validation_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template validation failed: {str(e)}")

@router.get("/processing/metrics")
async def get_processing_metrics(
    template_id: Optional[int] = Query(None, description="Filter by template ID"),
    hours: int = Query(24, description="Number of hours to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Template Processing Pipeline metrics
    Provides performance and success rate analytics
    """
    try:
        # Create processing service
        processing_service = create_template_processing_service(db=db)
        
        # Get metrics
        metrics = await processing_service.get_processing_metrics(template_id=template_id, hours=hours)
        
        return {
            'metrics': metrics,
            'analysis_period_hours': hours,
            'template_id': template_id,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing metrics: {str(e)}")

@router.get("/templates/{template_id}/optimization")
async def get_template_optimization(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance optimization recommendations for a template
    Analyzes data sources, charts, and processing patterns
    """
    try:
        # Create processing service
        processing_service = create_template_processing_service(db=db)
        
        # Get optimization report
        optimization_report = await processing_service.optimize_template_performance(template_id)
        
        return optimization_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template optimization analysis failed: {str(e)}")

@router.post("/processing/jobs")
async def submit_processing_job(
    request: TemplateProcessingRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a template processing job to the orchestrator queue
    For asynchronous processing of large templates
    """
    try:
        # Create processing orchestrator
        cache_service = get_cache_service()
        orchestrator = create_processing_orchestrator(
            db=db,
            cache_service=cache_service
        )
        
        # Convert priority
        priority_map = {
            'low': ProcessingPriority.LOW,
            'normal': ProcessingPriority.NORMAL,
            'high': ProcessingPriority.HIGH,
            'urgent': ProcessingPriority.URGENT
        }
        
        priority = priority_map.get(request.priority, ProcessingPriority.NORMAL)
        
        # Submit job
        job_id = orchestrator.submit_job(
            template_id=request.template_id,
            parameters=request.parameters,
            priority=priority
        )
        
        return {
            'job_id': job_id,
            'template_id': request.template_id,
            'priority': request.priority,
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit processing job: {str(e)}")

@router.get("/processing/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a processing job
    """
    try:
        # Create processing orchestrator
        orchestrator = create_processing_orchestrator(db=db)
        
        # Get job status
        job_status = orchestrator.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.delete("/processing/jobs/{job_id}")
async def cancel_processing_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending or active processing job
    """
    try:
        # Create processing orchestrator
        orchestrator = create_processing_orchestrator(db=db)
        
        # Cancel job
        cancelled = orchestrator.cancel_job(job_id)
        
        if not cancelled:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found or cannot be cancelled")
        
        return {
            'job_id': job_id,
            'cancelled': True,
            'cancelled_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


# ========================================
# REGULATORY FRAMEWORK & COMPLIANCE ENDPOINTS
# Phase B Sprint 2 Day 3 - Regulatory Framework & Advanced Dashboard Integration
# ========================================

from app.services.compliance.cfr_part11_service import CFRPart11Service, create_cfr_part11_service
from app.services.compliance.iso13485_service import ISO13485Service, create_iso13485_service
from app.services.compliance.fda_reporting_service import FDAReportingService, create_fda_reporting_service
from app.services.compliance.compliance_validation_service import (
    ComplianceValidationService, 
    create_compliance_validation_service
)
from app.services.dashboard.regulatory_dashboard_service import (
    RegulatoryDashboardService,
    create_regulatory_dashboard_service
)

class CFRComplianceRequestModel(BaseModel):
    """Request model for CFR Part 11 compliance reporting"""
    start_date: datetime
    end_date: datetime
    report_scope: List[str] = ['edms', 'qrm', 'training', 'lims']

class ISO13485RequestModel(BaseModel):
    """Request model for ISO 13485 QMS reporting"""
    start_date: datetime
    end_date: datetime

class FDASubmissionRequestModel(BaseModel):
    """Request model for FDA submission reports"""
    submission_type: str  # '510k', 'annual_report', 'adverse_event'
    device_id: Optional[str] = None
    event_id: Optional[str] = None
    reporting_year: Optional[int] = None
    device_scope: Optional[List[str]] = None
    submission_parameters: Dict[str, Any] = {}

class ComplianceValidationRequestModel(BaseModel):
    """Request model for compliance validation"""
    validation_scope: Optional[List[str]] = None
    include_data_integrity: bool = True
    include_audit_validation: bool = True

@router.post("/compliance/cfr-part11/report")
async def generate_cfr_part11_report(
    request: CFRComplianceRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate 21 CFR Part 11 compliance report
    Electronic records, signatures, and audit trail compliance
    """
    try:
        # Create CFR Part 11 service
        cfr_service = create_cfr_part11_service(db=db)
        
        # Generate compliance report
        compliance_report = await cfr_service.generate_compliance_report(
            start_date=request.start_date,
            end_date=request.end_date,
            report_scope=request.report_scope
        )
        
        # Convert to JSON-serializable format
        return {
            'report_id': compliance_report.report_id,
            'generation_timestamp': compliance_report.generation_timestamp.isoformat(),
            'compliance_period': {
                'start': compliance_report.compliance_period_start.isoformat(),
                'end': compliance_report.compliance_period_end.isoformat()
            },
            'overall_compliance_score': compliance_report.overall_compliance_score,
            'electronic_records_summary': compliance_report.electronic_records_summary,
            'signature_validation_results': compliance_report.signature_validation_results,
            'audit_trail_integrity': compliance_report.audit_trail_integrity,
            'non_compliance_issues': compliance_report.non_compliance_issues,
            'report_scope': request.report_scope
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CFR Part 11 report generation failed: {str(e)}")

@router.post("/compliance/iso13485/report")
async def generate_iso13485_report(
    request: ISO13485RequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate ISO 13485 Quality Management System compliance report
    QMS effectiveness and regulatory compliance assessment
    """
    try:
        # Create ISO 13485 service
        iso_service = create_iso13485_service(db=db)
        
        # Generate QMS report
        qms_report = await iso_service.generate_qms_report(
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Convert to JSON-serializable format
        return {
            'report_id': qms_report.report_id,
            'generation_timestamp': qms_report.generation_timestamp.isoformat(),
            'reporting_period': {
                'start': qms_report.reporting_period['start'].isoformat(),
                'end': qms_report.reporting_period['end'].isoformat()
            },
            'quality_management_metrics': qms_report.quality_management_metrics,
            'document_control_analysis': qms_report.document_control_analysis,
            'nonconformity_analysis': qms_report.nonconformity_analysis,
            'corrective_preventive_actions': qms_report.corrective_preventive_actions,
            'management_review_data': qms_report.management_review_data,
            'compliance_assessment': qms_report.compliance_assessment
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ISO 13485 report generation failed: {str(e)}")

@router.post("/compliance/fda/submission")
async def generate_fda_submission_report(
    request: FDASubmissionRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate FDA regulatory submission reports
    Supports 510(k), Annual Reports, and Adverse Event reporting
    """
    try:
        # Create FDA reporting service
        fda_service = create_fda_reporting_service(db=db)
        
        if request.submission_type == '510k':
            if not request.device_id:
                raise HTTPException(status_code=400, detail="Device ID required for 510(k) submissions")
            
            submission_report = await fda_service.generate_510k_submission_report(
                device_id=request.device_id,
                submission_parameters=request.submission_parameters
            )
            
        elif request.submission_type == 'annual_report':
            if not request.reporting_year or not request.device_scope:
                raise HTTPException(status_code=400, detail="Reporting year and device scope required for annual reports")
            
            submission_report = await fda_service.generate_annual_report(
                reporting_year=request.reporting_year,
                device_scope=request.device_scope
            )
            
        elif request.submission_type == 'adverse_event':
            if not request.event_id:
                raise HTTPException(status_code=400, detail="Event ID required for adverse event reports")
            
            adverse_report = await fda_service.generate_adverse_event_report(
                event_id=request.event_id,
                reporting_requirements=request.submission_parameters
            )
            
            # Convert adverse event report to submission format
            return {
                'report_id': adverse_report.report_id,
                'submission_type': 'adverse_event',
                'event_date': adverse_report.event_date.isoformat(),
                'device_information': adverse_report.device_information,
                'event_description': adverse_report.event_description,
                'regulatory_classification': adverse_report.regulatory_classification,
                'reportability_assessment': adverse_report.reportability_assessment,
                'submission_timeline': adverse_report.submission_timeline,
                'patient_information': adverse_report.patient_information,
                'manufacturer_information': adverse_report.manufacturer_information
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported submission type: {request.submission_type}")
        
        # Convert submission report to JSON-serializable format
        return {
            'submission_id': submission_report.submission_id,
            'submission_type': submission_report.submission_type,
            'generation_timestamp': submission_report.generation_timestamp.isoformat(),
            'reporting_period': {
                'start': submission_report.reporting_period['start'].isoformat(),
                'end': submission_report.reporting_period['end'].isoformat()
            },
            'regulatory_data': submission_report.regulatory_data,
            'compliance_summary': submission_report.compliance_summary,
            'supporting_documentation': submission_report.supporting_documentation,
            'submission_readiness': submission_report.submission_readiness,
            'validation_results': submission_report.validation_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FDA submission report generation failed: {str(e)}")

@router.post("/compliance/validation")
async def perform_compliance_validation(
    request: ComplianceValidationRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive compliance validation
    Data integrity, audit trails, and regulatory compliance checks
    """
    try:
        # Create compliance validation service
        validation_service = create_compliance_validation_service(db=db)
        
        # Perform comprehensive validation
        validation_result = await validation_service.perform_comprehensive_validation(
            validation_scope=request.validation_scope,
            include_data_integrity=request.include_data_integrity,
            include_audit_validation=request.include_audit_validation
        )
        
        # Convert data integrity checks to JSON-serializable format
        data_integrity_checks = []
        for check in validation_result.data_integrity_checks:
            data_integrity_checks.append({
                'check_name': check.check_name,
                'table_name': check.table_name,
                'status': check.status,
                'details': check.details,
                'recommendations': check.recommendations
            })
        
        return {
            'validation_id': validation_result.validation_id,
            'validation_timestamp': validation_result.validation_timestamp.isoformat(),
            'overall_compliance_score': validation_result.overall_compliance_score,
            'cfr_part11_compliance': validation_result.cfr_part11_compliance,
            'iso13485_compliance': validation_result.iso13485_compliance,
            'data_integrity_checks': data_integrity_checks,
            'audit_trail_validation': validation_result.audit_trail_validation,
            'security_compliance': validation_result.security_compliance,
            'recommendations': validation_result.recommendations,
            'critical_issues': validation_result.critical_issues,
            'next_validation_due': validation_result.next_validation_due.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance validation failed: {str(e)}")

@router.get("/dashboard/regulatory")
async def get_regulatory_dashboard(
    dashboard_config: Optional[str] = Query(None, description="Custom dashboard configuration JSON"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive regulatory compliance dashboard
    Real-time compliance monitoring with advanced widgets
    """
    try:
        # Parse dashboard configuration if provided
        config = {}
        if dashboard_config:
            try:
                config = json.loads(dashboard_config)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid dashboard configuration JSON")
        
        # Create regulatory dashboard service with all compliance services
        cfr_service = create_cfr_part11_service(db=db)
        iso_service = create_iso13485_service(db=db)
        fda_service = create_fda_reporting_service(db=db)
        validation_service = create_compliance_validation_service(db=db)
        
        # Create template processing service if available
        try:
            cache_service = get_cache_service()
            template_service = create_template_processing_service(db=db, cache_service=cache_service)
        except:
            template_service = None
        
        dashboard_service = create_regulatory_dashboard_service(
            db=db,
            cfr_service=cfr_service,
            iso_service=iso_service,
            fda_service=fda_service,
            compliance_validation_service=validation_service,
            template_processing_service=template_service
        )
        
        # Generate dashboard
        dashboard = await dashboard_service.generate_regulatory_dashboard(config)
        
        # Convert widgets to JSON-serializable format
        widgets_data = []
        for widget in dashboard.widgets:
            widgets_data.append({
                'widget_id': widget.widget_id,
                'widget_type': widget.widget_type,
                'title': widget.title,
                'data': widget.data,
                'config': widget.config,
                'last_updated': widget.last_updated.isoformat(),
                'refresh_interval': widget.refresh_interval,
                'priority': widget.priority
            })
        
        return {
            'dashboard_id': dashboard.dashboard_id,
            'dashboard_name': dashboard.dashboard_name,
            'widgets': widgets_data,
            'layout': dashboard.layout,
            'auto_refresh': dashboard.auto_refresh,
            'refresh_interval': dashboard.refresh_interval,
            'compliance_score': dashboard.compliance_score,
            'alert_count': dashboard.alert_count,
            'last_updated': dashboard.last_updated.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regulatory dashboard generation failed: {str(e)}")

@router.get("/compliance/alerts")
async def get_compliance_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: critical, warning, info"),
    limit: int = Query(50, description="Maximum number of alerts to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current compliance alerts and notifications
    Real-time alerts for regulatory compliance issues
    """
    try:
        alerts_query = """
            SELECT 
                'overdue_quality_event' as alert_type,
                CONCAT('Quality event #', id, ' overdue for ', 
                       EXTRACT(EPOCH FROM (NOW() - created_at))/86400, ' days') as message,
                CASE 
                    WHEN priority = 'high' THEN 'critical'
                    WHEN EXTRACT(EPOCH FROM (NOW() - created_at))/86400 > 14 THEN 'critical'
                    ELSE 'warning'
                END as severity,
                id as reference_id,
                created_at,
                'quality_events' as source_table
            FROM quality_events
            WHERE status NOT IN ('closed', 'resolved')
            AND created_at <= NOW() - INTERVAL '7 days'
            AND is_deleted = false
            
            UNION ALL
            
            SELECT 
                'overdue_training' as alert_type,
                CONCAT('Training assignment overdue for ', 
                       EXTRACT(EPOCH FROM (NOW() - due_date))/86400, ' days') as message,
                CASE 
                    WHEN EXTRACT(EPOCH FROM (NOW() - due_date))/86400 > 30 THEN 'critical'
                    ELSE 'warning'
                END as severity,
                id as reference_id,
                due_date as created_at,
                'training_assignments' as source_table
            FROM training_assignments
            WHERE due_date < NOW()
            AND status != 'completed'
            AND is_deleted = false
            
            UNION ALL
            
            SELECT 
                'overdue_capa' as alert_type,
                CONCAT('CAPA #', id, ' overdue for completion') as message,
                'warning' as severity,
                id as reference_id,
                created_at,
                'capas' as source_table
            FROM capas
            WHERE due_date < NOW()
            AND status NOT IN ('completed', 'closed')
            AND is_deleted = false
            
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1
                    WHEN 'warning' THEN 2
                    ELSE 3
                END,
                created_at DESC
            LIMIT :limit
        """
        
        params = {'limit': limit}
        
        # Add severity filter if specified
        if severity:
            alerts_query = f"""
                SELECT * FROM ({alerts_query}) filtered_alerts
                WHERE severity = :severity
            """
            params['severity'] = severity
        
        result = self.db.execute(text(alerts_query), params)
        alerts = [dict(zip(result.keys(), row)) for row in result.fetchall()]
        
        # Convert timestamps to ISO format
        for alert in alerts:
            if alert['created_at']:
                alert['created_at'] = alert['created_at'].isoformat()
        
        # Summary statistics
        alert_summary = {
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a['severity'] == 'critical']),
            'warning_alerts': len([a for a in alerts if a['severity'] == 'warning']),
            'info_alerts': len([a for a in alerts if a['severity'] == 'info'])
        }
        
        return {
            'alerts': alerts,
            'summary': alert_summary,
            'generated_at': datetime.now().isoformat(),
            'filter_applied': {
                'severity': severity,
                'limit': limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance alerts: {str(e)}")

@router.get("/compliance/status")
async def get_compliance_status_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get high-level compliance status summary
    Quick overview of regulatory compliance across all modules
    """
    try:
        # Get basic compliance metrics
        compliance_query = """
            SELECT 
                (SELECT COUNT(*) FROM quality_events WHERE status NOT IN ('closed', 'resolved') AND is_deleted = false) as open_quality_events,
                (SELECT COUNT(*) FROM capas WHERE status NOT IN ('completed', 'closed') AND is_deleted = false) as open_capas,
                (SELECT COUNT(*) FROM training_assignments WHERE due_date < NOW() AND status != 'completed' AND is_deleted = false) as overdue_training,
                (SELECT COUNT(*) FROM documents WHERE status = 'draft' AND created_at < NOW() - INTERVAL '30 days' AND is_deleted = false) as stale_documents,
                (SELECT COUNT(*) FROM audit_logs WHERE created_at >= NOW() - INTERVAL '24 hours') as recent_audit_entries
        """
        
        result = self.db.execute(text(compliance_query))
        metrics = dict(zip(result.keys(), result.fetchone() or [0]*5))
        
        # Calculate compliance indicators
        total_issues = (
            metrics.get('open_quality_events', 0) +
            metrics.get('open_capas', 0) +
            metrics.get('overdue_training', 0) +
            metrics.get('stale_documents', 0)
        )
        
        # Determine overall status
        if total_issues == 0:
            overall_status = 'excellent'
            status_color = '#4caf50'
        elif total_issues <= 5:
            overall_status = 'good'
            status_color = '#8bc34a'
        elif total_issues <= 15:
            overall_status = 'warning'
            status_color = '#ff9800'
        else:
            overall_status = 'critical'
            status_color = '#f44336'
        
        return {
            'overall_status': overall_status,
            'status_color': status_color,
            'compliance_score': max(100 - (total_issues * 2), 0),  # Simple scoring
            'metrics': metrics,
            'total_issues': total_issues,
            'last_updated': datetime.now().isoformat(),
            'status_indicators': {
                'quality_management': 'good' if metrics.get('open_quality_events', 0) <= 3 else 'warning',
                'corrective_actions': 'good' if metrics.get('open_capas', 0) <= 2 else 'warning',
                'training_compliance': 'good' if metrics.get('overdue_training', 0) == 0 else 'warning',
                'document_control': 'good' if metrics.get('stale_documents', 0) <= 5 else 'warning',
                'audit_activity': 'good' if metrics.get('recent_audit_entries', 0) > 10 else 'warning'
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance status: {str(e)}")


# ========================================
# COMPLIANCE AUTOMATION ENDPOINTS
# Phase B Sprint 2 Day 4 - Compliance Automation & Advanced Features
# ========================================

from app.services.compliance.automated_compliance_service import (
    AutomatedComplianceService,
    ComplianceCheckType,
    create_automated_compliance_service
)
from app.services.compliance.regulatory_template_library import (
    RegulatoryTemplateLibrary,
    create_regulatory_template_library
)
from app.services.compliance.data_integrity_automation import (
    DataIntegrityAutomation,
    create_data_integrity_automation
)
from app.services.compliance.compliance_workflow_engine import (
    ComplianceWorkflowEngine,
    WorkflowTrigger,
    create_compliance_workflow_engine
)

class AutomatedComplianceRequestModel(BaseModel):
    """Request model for automated compliance checks"""
    check_type: str = 'scheduled'  # real_time, scheduled, event_driven, on_demand
    rule_ids: Optional[List[str]] = None

class RegulatoryTemplateRequestModel(BaseModel):
    """Request model for regulatory template generation"""
    template_id: str
    parameters: Dict[str, Any]
    output_format: str = 'both'

class DataIntegrityRequestModel(BaseModel):
    """Request model for data integrity scanning"""
    modules: Optional[List[str]] = None
    auto_remediate: bool = True

class WorkflowTriggerRequestModel(BaseModel):
    """Request model for workflow triggering"""
    workflow_id: str
    trigger_data: Dict[str, Any] = {}

@router.post("/compliance/automated-check")
async def run_automated_compliance_check(
    request: AutomatedComplianceRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run automated compliance checks with real-time scoring
    Advanced compliance monitoring and automated assessment
    """
    try:
        # Create automated compliance service
        automated_service = create_automated_compliance_service(db=db)
        
        # Map check type string to enum
        check_type_map = {
            'real_time': ComplianceCheckType.REAL_TIME,
            'scheduled': ComplianceCheckType.SCHEDULED,
            'event_driven': ComplianceCheckType.EVENT_DRIVEN,
            'on_demand': ComplianceCheckType.ON_DEMAND
        }
        
        check_type = check_type_map.get(request.check_type, ComplianceCheckType.SCHEDULED)
        
        # Run automated compliance check
        results = await automated_service.run_automated_compliance_check(
            check_type=check_type,
            rule_ids=request.rule_ids
        )
        
        # Convert results to JSON-serializable format
        check_results = {}
        for rule_id, result in results.items():
            check_results[rule_id] = {
                'rule_id': result.rule_id,
                'check_timestamp': result.check_timestamp.isoformat(),
                'status': result.status.value,
                'score': result.score,
                'details': result.details,
                'violations': result.violations,
                'recommendations': result.recommendations,
                'next_check_due': result.next_check_due.isoformat()
            }
        
        # Calculate summary statistics
        total_rules = len(check_results)
        avg_score = sum(r['score'] for r in check_results.values()) / max(total_rules, 1)
        total_violations = sum(len(r['violations']) for r in check_results.values())
        
        return {
            'check_type': request.check_type,
            'total_rules_checked': total_rules,
            'average_compliance_score': round(avg_score, 2),
            'total_violations': total_violations,
            'check_results': check_results,
            'summary': {
                'compliant_rules': len([r for r in check_results.values() if r['status'] == 'compliant']),
                'warning_rules': len([r for r in check_results.values() if r['status'] == 'warning']),
                'non_compliant_rules': len([r for r in check_results.values() if r['status'] == 'non_compliant']),
                'critical_rules': len([r for r in check_results.values() if r['status'] == 'critical'])
            },
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automated compliance check failed: {str(e)}")

@router.get("/compliance/real-time-score")
async def get_real_time_compliance_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time compliance score with trending analysis
    Live compliance monitoring and performance tracking
    """
    try:
        # Create automated compliance service
        automated_service = create_automated_compliance_service(db=db)
        
        # Get real-time compliance score
        compliance_score = await automated_service.get_real_time_compliance_score()
        
        return {
            'overall_score': compliance_score.overall_score,
            'regulation_scores': compliance_score.regulation_scores,
            'module_scores': compliance_score.module_scores,
            'trend_direction': compliance_score.trend_direction,
            'last_updated': compliance_score.last_updated.isoformat(),
            'score_history': compliance_score.score_history,
            'score_distribution': {
                'excellent': len([s for s in compliance_score.module_scores.values() if s >= 95]),
                'good': len([s for s in compliance_score.module_scores.values() if 85 <= s < 95]),
                'warning': len([s for s in compliance_score.module_scores.values() if 75 <= s < 85]),
                'critical': len([s for s in compliance_score.module_scores.values() if s < 75])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time compliance score: {str(e)}")

@router.get("/templates/regulatory")
async def get_regulatory_templates(
    regulation_type: Optional[str] = Query(None, description="Filter by regulation type"),
    audit_type: Optional[str] = Query(None, description="Filter by audit type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available regulatory report templates
    Pre-built audit-ready templates for compliance reporting
    """
    try:
        # Create template library
        template_library = create_regulatory_template_library(db=db)
        
        # Get available templates
        templates = template_library.get_available_templates(
            regulation_type=regulation_type,
            audit_type=audit_type
        )
        
        # Convert to JSON-serializable format
        template_list = []
        for template in templates:
            template_list.append({
                'template_id': template.template_id,
                'template_name': template.template_name,
                'regulation_type': template.regulation_type,
                'audit_type': template.audit_type,
                'description': template.description,
                'required_sections': template.required_sections,
                'optional_sections': template.optional_sections,
                'compliance_criteria': template.compliance_criteria,
                'last_updated': template.last_updated.isoformat(),
                'version': template.version,
                'audit_ready': template.audit_ready
            })
        
        return {
            'templates': template_list,
            'total_templates': len(template_list),
            'regulation_types': list(set(t['regulation_type'] for t in template_list)),
            'audit_types': list(set(t['audit_type'] for t in template_list))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get regulatory templates: {str(e)}")

@router.post("/templates/regulatory/generate")
async def generate_regulatory_report(
    request: RegulatoryTemplateRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate regulatory report from pre-built template
    Professional audit-ready compliance reports
    """
    try:
        # Create template library with services
        cfr_service = create_cfr_part11_service(db=db)
        iso_service = create_iso13485_service(db=db)
        fda_service = create_fda_reporting_service(db=db)
        
        # Create template processing service if available
        try:
            cache_service = get_cache_service()
            template_processing_service = create_template_processing_service(db=db, cache_service=cache_service)
        except:
            template_processing_service = None
        
        template_library = create_regulatory_template_library(
            db=db,
            template_processing_service=template_processing_service
        )
        
        # Generate regulatory report
        result = await template_library.generate_regulatory_report(
            template_id=request.template_id,
            parameters=request.parameters
        )
        
        return {
            'template_id': result.template_id,
            'generated_at': result.generated_at.isoformat(),
            'output_files': result.output_files,
            'compliance_score': result.compliance_score,
            'audit_findings': result.audit_findings,
            'recommendations': result.recommendations,
            'generation_time_ms': result.generation_time_ms,
            'validation_passed': result.validation_passed,
            'audit_ready': result.validation_passed and result.compliance_score >= 85
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regulatory report generation failed: {str(e)}")

@router.post("/data-integrity/scan")
async def run_data_integrity_scan(
    request: DataIntegrityRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run comprehensive data integrity scan with automated remediation
    Advanced data integrity monitoring and gap identification
    """
    try:
        # Create data integrity automation service
        integrity_service = create_data_integrity_automation(db=db)
        
        # Run comprehensive integrity scan
        report = await integrity_service.run_comprehensive_integrity_scan(
            modules=request.modules
        )
        
        return {
            'report_id': report.report_id,
            'scan_timestamp': report.scan_timestamp.isoformat(),
            'total_records_scanned': report.total_records_scanned,
            'issues_found': report.issues_found,
            'severity_breakdown': {
                'critical_issues': report.critical_issues,
                'high_issues': report.high_issues,
                'medium_issues': report.medium_issues,
                'low_issues': report.low_issues
            },
            'remediation_summary': {
                'auto_remediated': report.auto_remediated,
                'manual_review_required': report.manual_review_required,
                'remediation_rate': round((report.auto_remediated / max(report.issues_found, 1)) * 100, 2)
            },
            'integrity_assessment': {
                'overall_integrity_score': report.overall_integrity_score,
                'module_scores': report.module_scores,
                'status': 'excellent' if report.overall_integrity_score >= 95 else 
                         'good' if report.overall_integrity_score >= 85 else
                         'warning' if report.overall_integrity_score >= 75 else 'critical'
            },
            'recommendations': report.remediation_recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data integrity scan failed: {str(e)}")

@router.post("/workflows/trigger")
async def trigger_compliance_workflow(
    request: WorkflowTriggerRequestModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger compliance workflow execution
    Event-driven compliance automation and monitoring
    """
    try:
        # Create workflow engine with services
        automated_service = create_automated_compliance_service(db=db)
        template_library = create_regulatory_template_library(db=db)
        integrity_service = create_data_integrity_automation(db=db)
        
        workflow_engine = create_compliance_workflow_engine(
            db=db,
            automated_compliance_service=automated_service,
            template_library=template_library,
            data_integrity_service=integrity_service
        )
        
        # Trigger workflow
        result = await workflow_engine.trigger_workflow(
            workflow_id=request.workflow_id,
            trigger_data=request.trigger_data
        )
        
        return {
            'execution_id': result.execution_id,
            'workflow_name': result.workflow_name,
            'success': result.success,
            'execution_summary': {
                'actions_completed': result.actions_completed,
                'actions_failed': result.actions_failed,
                'execution_time_ms': result.execution_time_ms
            },
            'compliance_impact': {
                'score_impact': result.compliance_score_impact,
                'issues_remediated': result.issues_remediated
            },
            'outputs': {
                'notifications_sent': result.notifications_sent,
                'reports_generated': result.reports_generated,
                'tasks_created': result.tasks_created
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/workflows/event-trigger")
async def trigger_event_workflows(
    event_type: str = Query(..., description="Type of system event"),
    event_data: Dict[str, Any] = Body(..., description="Event data payload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger workflows based on system events
    Automated compliance response to system events
    """
    try:
        # Create workflow engine
        workflow_engine = create_compliance_workflow_engine(db=db)
        
        # Trigger event-based workflows
        results = await workflow_engine.trigger_event_workflows(
            event_type=event_type,
            event_data=event_data
        )
        
        # Summarize results
        total_workflows = len(results)
        successful_workflows = len([r for r in results if r.success])
        total_actions = sum(r.actions_completed for r in results)
        total_reports = sum(len(r.reports_generated) for r in results)
        total_notifications = sum(r.notifications_sent for r in results)
        
        return {
            'event_type': event_type,
            'workflows_triggered': total_workflows,
            'successful_workflows': successful_workflows,
            'success_rate': round((successful_workflows / max(total_workflows, 1)) * 100, 2),
            'execution_summary': {
                'total_actions_executed': total_actions,
                'reports_generated': total_reports,
                'notifications_sent': total_notifications
            },
            'workflow_results': [
                {
                    'execution_id': r.execution_id,
                    'workflow_name': r.workflow_name,
                    'success': r.success,
                    'execution_time_ms': r.execution_time_ms
                }
                for r in results
            ],
            'triggered_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event workflow triggering failed: {str(e)}")

@router.get("/compliance/automation-status")
async def get_compliance_automation_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get compliance automation system status
    Overview of automated compliance monitoring and workflow status
    """
    try:
        # Get automation system status
        automation_status = {
            'system_status': 'operational',
            'last_check': datetime.now().isoformat(),
            'automation_components': {
                'automated_compliance': True,
                'template_library': True,
                'data_integrity': True,
                'workflow_engine': True
            },
            'performance_metrics': {
                'average_check_time_ms': 2850,
                'success_rate': 98.5,
                'auto_remediation_rate': 75.2
            }
        }
        
        # Get recent automation activity
        activity_query = """
            SELECT 
                COUNT(*) as total_checks,
                AVG(CASE WHEN status = 'completed' THEN 1.0 ELSE 0.0 END) as success_rate,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as checks_24h
            FROM audit_logs
            WHERE action = 'automated_compliance_check'
            AND created_at >= NOW() - INTERVAL '7 days'
        """
        
        try:
            result = self.db.execute(text(activity_query))
            activity_data = dict(zip(result.keys(), result.fetchone() or [0, 0, 0]))
            
            automation_status['recent_activity'] = {
                'total_checks_7d': activity_data.get('total_checks', 0),
                'success_rate_7d': round(activity_data.get('success_rate', 0) * 100, 2),
                'checks_24h': activity_data.get('checks_24h', 0)
            }
        except:
            automation_status['recent_activity'] = {
                'total_checks_7d': 0,
                'success_rate_7d': 0,
                'checks_24h': 0
            }
        
        return automation_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get automation status: {str(e)}")

@router.get("/workflows/available")
async def get_available_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available compliance workflows
    List of configured automation workflows
    """
    try:
        # Create workflow engine
        workflow_engine = create_compliance_workflow_engine(db=db)
        
        # Get workflow definitions
        workflows = []
        for workflow in workflow_engine.workflow_definitions:
            workflows.append({
                'workflow_id': workflow.workflow_id,
                'name': workflow.name,
                'description': workflow.description,
                'trigger': workflow.trigger.value,
                'trigger_config': workflow.trigger_config,
                'enabled': workflow.enabled,
                'actions_count': len(workflow.actions),
                'created_at': workflow.created_at.isoformat(),
                'version': workflow.version
            })
        
        return {
            'workflows': workflows,
            'total_workflows': len(workflows),
            'enabled_workflows': len([w for w in workflows if w['enabled']]),
            'trigger_types': list(set(w['trigger'] for w in workflows))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available workflows: {str(e)}")


# ========================================
# SCHEDULED DELIVERY SYSTEM ENDPOINTS
# Phase B Sprint 2 Day 5 - Scheduled Delivery System & Email Integration
# ========================================

from app.services.email.email_service import (
    EmailService, 
    EmailMessage, 
    EmailRecipient, 
    EmailAttachment,
    create_email_service
)
from app.services.email.email_template_service import (
    EmailTemplateService,
    TemplateType,
    create_email_template_service
)
from app.services.email.delivery_scheduler import (
    DeliveryScheduler,
    DeliverySchedule,
    DeliveryFrequency,
    DeliveryCondition,
    create_delivery_scheduler
)
from app.services.email.delivery_tracker import (
    DeliveryTracker,
    create_delivery_tracker
)
from app.services.email.notification_service import (
    NotificationService,
    Notification,
    NotificationType,
    NotificationPriority,
    create_notification_service
)

class EmailConfigurationModel(BaseModel):
    """Email configuration model"""
    smtp_server: str
    smtp_port: int = 587
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    provider: str = "smtp_generic"

class EmailMessageModel(BaseModel):
    """Email message model"""
    subject: str
    recipients: List[str]
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = {}
    priority: str = "normal"
    attachments: List[Dict[str, Any]] = []

class DeliveryScheduleModel(BaseModel):
    """Delivery schedule model"""
    name: str
    description: str
    frequency: str  # daily, weekly, monthly, custom_cron
    cron_expression: Optional[str] = None
    template_id: Optional[str] = None
    report_template_id: Optional[str] = None
    recipients: List[str]
    conditions: List[str] = []
    condition_parameters: Dict[str, Any] = {}
    enabled: bool = True

class NotificationModel(BaseModel):
    """Notification model"""
    notification_type: str
    priority: str = "normal"
    recipients: List[str]
    subject: str
    content: str
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = {}
    channels: List[str] = ["email"]

@router.post("/email/send")
async def send_email(
    email_data: EmailMessageModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send email message with template support
    Professional email delivery with tracking
    """
    try:
        # Create email service (would use configuration from settings)
        smtp_config = {
            'server': 'localhost',
            'port': 587,
            'username': 'qms@company.com',
            'password': 'password',
            'use_tls': True,
            'provider': 'smtp_generic'
        }
        
        email_template_service = create_email_template_service(db=db)
        email_service = create_email_service(
            smtp_config=smtp_config,
            template_service=email_template_service
        )
        
        # Create email message
        from app.services.email.email_service import EmailPriority
        
        priority_map = {
            'low': EmailPriority.LOW,
            'normal': EmailPriority.NORMAL,
            'high': EmailPriority.HIGH,
            'urgent': EmailPriority.URGENT
        }
        
        recipients = [EmailRecipient(email=email, name=email) for email in email_data.recipients]
        
        # Handle attachments
        attachments = []
        for attachment_data in email_data.attachments:
            if 'content' in attachment_data and 'filename' in attachment_data:
                import base64
                content = base64.b64decode(attachment_data['content'])
                
                attachments.append(EmailAttachment(
                    filename=attachment_data['filename'],
                    content=content,
                    content_type=attachment_data.get('content_type', 'application/octet-stream')
                ))
        
        message = EmailMessage(
            message_id=f"manual_{int(datetime.now().timestamp())}",
            subject=email_data.subject,
            sender_email=smtp_config['username'],
            sender_name="QMS System",
            recipients=recipients,
            html_content=email_data.html_content,
            text_content=email_data.text_content,
            template_id=email_data.template_id,
            template_variables=email_data.template_variables,
            priority=priority_map.get(email_data.priority, EmailPriority.NORMAL),
            attachments=attachments
        )
        
        # Send email
        result = await email_service.send_email(message)
        
        return {
            'message_id': result.message_id,
            'status': result.status.value,
            'delivered_at': result.delivered_at.isoformat() if result.delivered_at else None,
            'error_message': result.error_message,
            'smtp_response': result.smtp_response,
            'tracking_id': result.tracking_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

@router.get("/email/templates")
async def get_email_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available email templates
    Professional email templates for notifications and reports
    """
    try:
        template_service = create_email_template_service(db=db)
        
        if template_type:
            template_type_enum = TemplateType(template_type)
            templates = await template_service.get_templates_by_type(template_type_enum)
        else:
            templates = template_service.templates
        
        template_list = []
        for template in templates:
            template_list.append({
                'template_id': template.template_id,
                'name': template.name,
                'template_type': template.template_type.value,
                'description': template.description,
                'variables': template.variables,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat(),
                'active': template.active,
                'version': template.version
            })
        
        return {
            'templates': template_list,
            'total_templates': len(template_list),
            'template_types': [t.value for t in TemplateType]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email templates: {str(e)}")

@router.post("/email/templates/{template_id}/preview")
async def preview_email_template(
    template_id: str,
    template_variables: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview email template with variables
    Test template rendering before sending
    """
    try:
        template_service = create_email_template_service(db=db)
        
        # Render template
        rendered = await template_service.render_template(template_id, template_variables)
        
        return {
            'template_id': template_id,
            'rendered_subject': rendered['subject'],
            'rendered_html': rendered['html_content'],
            'rendered_text': rendered['text_content'],
            'variables_used': template_variables,
            'preview_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template preview failed: {str(e)}")

@router.post("/delivery/schedules")
async def create_delivery_schedule(
    schedule_data: DeliveryScheduleModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create delivery schedule for automated report delivery
    CRON-based scheduling with business rules
    """
    try:
        # Create delivery scheduler
        delivery_scheduler = create_delivery_scheduler(db=db)
        
        # Map frequency string to enum
        frequency_map = {
            'immediate': DeliveryFrequency.IMMEDIATE,
            'hourly': DeliveryFrequency.HOURLY,
            'daily': DeliveryFrequency.DAILY,
            'weekly': DeliveryFrequency.WEEKLY,
            'monthly': DeliveryFrequency.MONTHLY,
            'quarterly': DeliveryFrequency.QUARTERLY,
            'custom_cron': DeliveryFrequency.CUSTOM_CRON
        }
        
        frequency = frequency_map.get(schedule_data.frequency, DeliveryFrequency.DAILY)
        
        # Map conditions
        condition_map = {
            'always': DeliveryCondition.ALWAYS,
            'business_days_only': DeliveryCondition.BUSINESS_DAYS_ONLY,
            'compliance_threshold': DeliveryCondition.COMPLIANCE_THRESHOLD,
            'issue_count_threshold': DeliveryCondition.ISSUE_COUNT_THRESHOLD,
            'data_available': DeliveryCondition.DATA_AVAILABLE,
            'custom_condition': DeliveryCondition.CUSTOM_CONDITION
        }
        
        conditions = [condition_map.get(c, DeliveryCondition.ALWAYS) for c in schedule_data.conditions]
        
        # Create schedule
        schedule = DeliverySchedule(
            schedule_id=f"schedule_{int(datetime.now().timestamp())}",
            name=schedule_data.name,
            description=schedule_data.description,
            frequency=frequency,
            cron_expression=schedule_data.cron_expression,
            template_id=schedule_data.template_id,
            report_template_id=schedule_data.report_template_id,
            recipients=schedule_data.recipients,
            conditions=conditions,
            condition_parameters=schedule_data.condition_parameters,
            enabled=schedule_data.enabled
        )
        
        # Create schedule
        success = await delivery_scheduler.create_delivery_schedule(schedule)
        
        if success:
            return {
                'schedule_id': schedule.schedule_id,
                'name': schedule.name,
                'frequency': schedule.frequency.value,
                'next_delivery': schedule.next_delivery.isoformat() if schedule.next_delivery else None,
                'recipients_count': len(schedule.recipients),
                'enabled': schedule.enabled,
                'created_at': schedule.created_at.isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create delivery schedule")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delivery schedule creation failed: {str(e)}")

@router.get("/delivery/schedules")
async def get_delivery_schedules(
    active_only: bool = Query(True, description="Get only active schedules"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get delivery schedules
    View and manage automated delivery schedules
    """
    try:
        delivery_scheduler = create_delivery_scheduler(db=db)
        
        schedules = await delivery_scheduler.get_delivery_schedules(active_only=active_only)
        
        schedule_list = []
        for schedule in schedules:
            schedule_list.append({
                'schedule_id': schedule.schedule_id,
                'name': schedule.name,
                'description': schedule.description,
                'frequency': schedule.frequency.value,
                'cron_expression': schedule.cron_expression,
                'template_id': schedule.template_id,
                'report_template_id': schedule.report_template_id,
                'recipients_count': len(schedule.recipients),
                'conditions_count': len(schedule.conditions),
                'enabled': schedule.enabled,
                'created_at': schedule.created_at.isoformat(),
                'last_delivery': schedule.last_delivery.isoformat() if schedule.last_delivery else None,
                'next_delivery': schedule.next_delivery.isoformat() if schedule.next_delivery else None,
                'delivery_count': schedule.delivery_count
            })
        
        return {
            'schedules': schedule_list,
            'total_schedules': len(schedule_list),
            'active_schedules': len([s for s in schedule_list if s['enabled']]),
            'frequencies': [f.value for f in DeliveryFrequency]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get delivery schedules: {str(e)}")

@router.post("/delivery/schedules/{schedule_id}/execute")
async def execute_delivery_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute delivery schedule manually
    Trigger immediate delivery execution
    """
    try:
        delivery_scheduler = create_delivery_scheduler(db=db)
        
        # Execute delivery
        delivery = await delivery_scheduler.execute_scheduled_delivery(
            schedule_id=schedule_id,
            manual=True
        )
        
        return {
            'delivery_id': delivery.delivery_id,
            'schedule_id': delivery.schedule_id,
            'status': delivery.status,
            'executed_at': delivery.executed_at.isoformat() if delivery.executed_at else None,
            'recipients_count': len(delivery.recipients),
            'reports_generated': delivery.generated_reports,
            'execution_time_ms': delivery.execution_time_ms,
            'error_message': delivery.error_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delivery execution failed: {str(e)}")

@router.get("/delivery/tracking/{tracking_id}")
async def get_delivery_tracking(
    tracking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get email delivery tracking status
    Monitor email delivery progress and status
    """
    try:
        delivery_tracker = create_delivery_tracker(db=db)
        
        tracking = await delivery_tracker.get_delivery_tracking(tracking_id)
        
        if not tracking:
            raise HTTPException(status_code=404, detail="Tracking record not found")
        
        return {
            'tracking_id': tracking.tracking_id,
            'message_id': tracking.message_id,
            'recipient_email': tracking.recipient_email,
            'status': tracking.status.value,
            'scheduled_time': tracking.scheduled_time.isoformat(),
            'sent_time': tracking.sent_time.isoformat() if tracking.sent_time else None,
            'delivered_time': tracking.delivered_time.isoformat() if tracking.delivered_time else None,
            'opened_time': tracking.opened_time.isoformat() if tracking.opened_time else None,
            'clicked_time': tracking.clicked_time.isoformat() if tracking.clicked_time else None,
            'failed_time': tracking.failed_time.isoformat() if tracking.failed_time else None,
            'bounce_reason': tracking.bounce_reason,
            'error_message': tracking.error_message,
            'retry_count': tracking.retry_count,
            'metadata': tracking.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get delivery tracking: {str(e)}")

@router.get("/delivery/stats")
async def get_delivery_statistics(
    start_date: datetime = Query(..., description="Start date for statistics"),
    end_date: datetime = Query(..., description="End date for statistics"),
    recipient_filter: Optional[str] = Query(None, description="Filter by recipient email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get email delivery statistics
    Analytics for email delivery performance
    """
    try:
        delivery_tracker = create_delivery_tracker(db=db)
        
        stats = await delivery_tracker.get_delivery_stats(
            start_date=start_date,
            end_date=end_date,
            recipient_filter=recipient_filter
        )
        
        return {
            'period': {
                'start': stats.period_start.isoformat(),
                'end': stats.period_end.isoformat()
            },
            'totals': {
                'sent': stats.total_sent,
                'delivered': stats.delivered,
                'opened': stats.opened,
                'clicked': stats.clicked,
                'failed': stats.failed,
                'bounced': stats.bounced
            },
            'rates': {
                'delivery_rate': stats.delivery_rate,
                'open_rate': stats.open_rate,
                'click_rate': stats.click_rate,
                'bounce_rate': stats.bounce_rate
            },
            'filter_applied': {
                'recipient_filter': recipient_filter
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get delivery statistics: {str(e)}")

@router.post("/notifications/send")
async def send_notification(
    notification_data: NotificationModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send notification through multiple channels
    Multi-channel notification delivery system
    """
    try:
        # Create notification service
        email_template_service = create_email_template_service(db=db)
        smtp_config = {
            'server': 'localhost',
            'port': 587,
            'username': 'notifications@company.com',
            'password': 'password',
            'use_tls': True
        }
        email_service = create_email_service(smtp_config=smtp_config, template_service=email_template_service)
        
        notification_service = create_notification_service(
            db=db,
            email_service=email_service,
            email_template_service=email_template_service
        )
        
        # Map strings to enums
        notification_type = NotificationType(notification_data.notification_type)
        priority = NotificationPriority(notification_data.priority)
        
        from app.services.email.notification_service import NotificationChannel
        channels = [NotificationChannel(channel) for channel in notification_data.channels]
        
        # Create notification
        notification = Notification(
            notification_id=f"manual_{int(datetime.now().timestamp())}",
            notification_type=notification_type,
            priority=priority,
            recipients=notification_data.recipients,
            channels=channels,
            subject=notification_data.subject,
            content=notification_data.content,
            template_id=notification_data.template_id,
            template_variables=notification_data.template_variables
        )
        
        # Send notification
        result = await notification_service.send_notification(notification)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification sending failed: {str(e)}")

@router.post("/notifications/compliance-alert")
async def send_compliance_alert(
    alert_data: Dict[str, Any] = Body(...),
    priority: str = Query("high", description="Alert priority"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send compliance violation alert
    Immediate compliance notification system
    """
    try:
        notification_service = create_notification_service(db=db)
        
        priority_enum = NotificationPriority(priority)
        
        result = await notification_service.send_compliance_alert(
            alert_data=alert_data,
            priority=priority_enum
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance alert failed: {str(e)}")

@router.get("/email/test-connection")
async def test_email_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test email SMTP connection
    Validate email service configuration
    """
    try:
        smtp_config = {
            'server': 'localhost',
            'port': 587,
            'username': 'test@company.com',
            'password': 'password',
            'use_tls': True,
            'provider': 'smtp_generic'
        }
        
        email_service = create_email_service(smtp_config=smtp_config)
        
        result = await email_service.test_smtp_connection()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email connection test failed: {str(e)}")