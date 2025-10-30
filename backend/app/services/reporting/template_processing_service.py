# Template Processing Service - Phase B Sprint 2 Day 2
# Unified service that integrates all Template Processing Pipeline components

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
import logging
import json
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from .data_aggregator import DataAggregationService, DataSource, AggregationResult
from .template_validator import TemplateValidationService, ValidationResult
from .enhanced_chart_service import EnhancedChartService, ChartGenerationResult
from .cache_service import ReportCacheService
from .pdf_generator import PDFGenerationService
from .excel_generator import ExcelGenerationService

logger = logging.getLogger(__name__)

@dataclass
class TemplateProcessingRequest:
    """Request for template processing"""
    template_id: int
    parameters: Dict[str, Any]
    output_format: str = 'both'  # 'pdf', 'excel', 'both'
    validate_template: bool = True
    generate_charts: bool = True
    cache_results: bool = True
    priority: str = 'normal'  # 'low', 'normal', 'high', 'urgent'

@dataclass
class TemplateProcessingResult:
    """Result of template processing"""
    success: bool
    template_id: int
    processing_id: str
    generated_files: List[str] = field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    aggregation_result: Optional[AggregationResult] = None
    chart_results: List[ChartGenerationResult] = field(default_factory=list)
    processing_time_ms: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TemplateProcessingService:
    """
    Unified Template Processing Service
    Orchestrates validation, data aggregation, chart generation, and report creation
    """
    
    def __init__(self, 
                 db: Session,
                 cache_service: Optional[ReportCacheService] = None,
                 pdf_generator: Optional[PDFGenerationService] = None,
                 excel_generator: Optional[ExcelGenerationService] = None):
        self.db = db
        self.cache_service = cache_service
        self.pdf_generator = pdf_generator
        self.excel_generator = excel_generator
        
        # Initialize component services
        self.data_aggregator = DataAggregationService(db=db, cache_service=cache_service)
        self.template_validator = TemplateValidationService(db=db, data_aggregator=self.data_aggregator)
        self.chart_service = EnhancedChartService(cache_service=cache_service)
        
    async def process_template(self, request: TemplateProcessingRequest) -> TemplateProcessingResult:
        """
        Process a complete template with all pipeline stages
        
        Args:
            request: Template processing request
            
        Returns:
            Complete processing result
        """
        start_time = datetime.now()
        processing_id = f"proc_{request.template_id}_{int(datetime.now().timestamp())}"
        
        logger.info(f"Starting template processing {processing_id} for template {request.template_id}")
        
        try:
            result = TemplateProcessingResult(
                success=True,
                template_id=request.template_id,
                processing_id=processing_id,
                metadata={
                    'start_time': start_time.isoformat(),
                    'parameters': request.parameters,
                    'output_format': request.output_format
                }
            )
            
            # Stage 1: Template Validation
            if request.validate_template:
                logger.info(f"Processing {processing_id}: Stage 1 - Template Validation")
                validation_result = await self._validate_template(request.template_id)
                result.validation_result = validation_result
                
                if not validation_result.is_valid:
                    raise Exception(f"Template validation failed: {validation_result.error_count} errors")
            
            # Stage 2: Data Aggregation
            logger.info(f"Processing {processing_id}: Stage 2 - Data Aggregation")
            template_config = await self._get_template_configuration(request.template_id)
            aggregation_result = await self._aggregate_template_data(
                template_config, request.parameters, request.template_id
            )
            result.aggregation_result = aggregation_result
            
            if not aggregation_result.success:
                raise Exception(f"Data aggregation failed: {'; '.join(aggregation_result.errors)}")
            
            # Stage 3: Chart Generation
            chart_results = []
            if request.generate_charts:
                logger.info(f"Processing {processing_id}: Stage 3 - Chart Generation")
                chart_results = await self._generate_template_charts(
                    template_config, aggregation_result.data, request.template_id
                )
                result.chart_results = chart_results
            
            # Stage 4: Report Generation
            logger.info(f"Processing {processing_id}: Stage 4 - Report Generation")
            generated_files = await self._generate_reports(
                request, template_config, aggregation_result.data, chart_results
            )
            result.generated_files = generated_files
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result.processing_time_ms = processing_time
            result.metadata['end_time'] = datetime.now().isoformat()
            result.metadata['processing_stages'] = 4
            
            logger.info(f"Template processing {processing_id} completed successfully in {processing_time}ms")
            
            return result
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = str(e)
            
            logger.error(f"Template processing {processing_id} failed: {error_msg}")
            
            return TemplateProcessingResult(
                success=False,
                template_id=request.template_id,
                processing_id=processing_id,
                processing_time_ms=processing_time,
                error_message=error_msg,
                metadata={
                    'start_time': start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'error_stage': self._determine_error_stage(e)
                }
            )
    
    async def _validate_template(self, template_id: int) -> ValidationResult:
        """Validate template configuration"""
        
        try:
            # Run validation without performance tests for speed
            validation_result = self.template_validator.validate_template(
                template_id, run_tests=False
            )
            return validation_result
            
        except Exception as e:
            logger.error(f"Template validation failed for {template_id}: {str(e)}")
            raise e
    
    async def _get_template_configuration(self, template_id: int) -> Dict[str, Any]:
        """Get template configuration from database"""
        
        from sqlalchemy import text
        
        query = """
            SELECT 
                id, name, description, report_type, configuration, 
                parameters_schema, created_at, updated_at
            FROM report_templates
            WHERE id = :template_id AND is_deleted = false
        """
        
        result = self.db.execute(text(query), {'template_id': template_id})
        row = result.fetchone()
        
        if not row:
            raise Exception(f"Template {template_id} not found")
        
        template = dict(zip(result.keys(), row))
        
        # Parse JSON fields
        if template['configuration']:
            template['configuration'] = json.loads(template['configuration'])
        if template['parameters_schema']:
            template['parameters_schema'] = json.loads(template['parameters_schema'])
        
        return template
    
    async def _aggregate_template_data(self, 
                                     template_config: Dict[str, Any], 
                                     parameters: Dict[str, Any],
                                     template_id: int) -> AggregationResult:
        """Aggregate data for template"""
        
        try:
            # Extract data sources from template configuration
            config = template_config.get('configuration', {})
            data_sources_config = config.get('data_sources', [])
            
            if not data_sources_config:
                logger.warning(f"No data sources configured for template {template_id}")
                return AggregationResult(
                    success=True,
                    data={'raw_data': {}, 'metadata': {'sources_count': 0}},
                    sources_collected=[],
                    sources_failed=[],
                    collection_time_ms=0,
                    cache_hits=0,
                    cache_misses=0,
                    errors=[]
                )
            
            # Convert to DataSource objects
            data_sources = []
            for source_config in data_sources_config:
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
            aggregation_result = await self.data_aggregator.aggregate_report_data(
                data_sources, parameters, template_id
            )
            
            return aggregation_result
            
        except Exception as e:
            logger.error(f"Data aggregation failed for template {template_id}: {str(e)}")
            raise e
    
    async def _generate_template_charts(self, 
                                      template_config: Dict[str, Any],
                                      aggregated_data: Dict[str, Any],
                                      template_id: int) -> List[ChartGenerationResult]:
        """Generate charts for template"""
        
        try:
            # Extract chart configurations
            config = template_config.get('configuration', {})
            charts_config = config.get('charts', [])
            
            if not charts_config:
                logger.info(f"No charts configured for template {template_id}")
                return []
            
            # Generate charts concurrently
            chart_results = await self.chart_service.generate_multiple_charts(
                charts_config, aggregated_data
            )
            
            # Log results
            successful_charts = len([r for r in chart_results if r.success])
            logger.info(f"Chart generation for template {template_id}: {successful_charts}/{len(charts_config)} successful")
            
            return chart_results
            
        except Exception as e:
            logger.error(f"Chart generation failed for template {template_id}: {str(e)}")
            raise e
    
    async def _generate_reports(self, 
                              request: TemplateProcessingRequest,
                              template_config: Dict[str, Any],
                              aggregated_data: Dict[str, Any],
                              chart_results: List[ChartGenerationResult]) -> List[str]:
        """Generate final reports"""
        
        generated_files = []
        
        try:
            # Prepare report data
            report_data = {
                'template': template_config,
                'parameters': request.parameters,
                'data': aggregated_data,
                'charts': {result.chart_id: result for result in chart_results if result.success},
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'processing_id': f"proc_{request.template_id}_{int(datetime.now().timestamp())}",
                    'total_charts': len(chart_results),
                    'successful_charts': len([r for r in chart_results if r.success])
                }
            }
            
            # Generate PDF if requested
            if request.output_format in ['pdf', 'both'] and self.pdf_generator:
                pdf_path = await self._generate_pdf_report(request, report_data)
                if pdf_path:
                    generated_files.append(pdf_path)
            
            # Generate Excel if requested
            if request.output_format in ['excel', 'both'] and self.excel_generator:
                excel_path = await self._generate_excel_report(request, report_data)
                if excel_path:
                    generated_files.append(excel_path)
            
            return generated_files
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise e
    
    async def _generate_pdf_report(self, request: TemplateProcessingRequest, report_data: Dict[str, Any]) -> Optional[str]:
        """Generate PDF report"""
        
        if not self.pdf_generator:
            logger.warning("PDF generator not available")
            return None
        
        try:
            output_path = f"reports/template_{request.template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            await self.pdf_generator.generate_report(
                template_id=request.template_id,
                data=report_data,
                output_path=output_path,
                parameters=request.parameters
            )
            
            logger.info(f"PDF report generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise e
    
    async def _generate_excel_report(self, request: TemplateProcessingRequest, report_data: Dict[str, Any]) -> Optional[str]:
        """Generate Excel report"""
        
        if not self.excel_generator:
            logger.warning("Excel generator not available")
            return None
        
        try:
            output_path = f"reports/template_{request.template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            await self.excel_generator.generate_report(
                template_id=request.template_id,
                data=report_data,
                output_path=output_path,
                parameters=request.parameters
            )
            
            logger.info(f"Excel report generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Excel generation failed: {str(e)}")
            raise e
    
    def _determine_error_stage(self, error: Exception) -> str:
        """Determine which stage the error occurred in"""
        
        error_str = str(error).lower()
        
        if 'validation' in error_str:
            return 'template_validation'
        elif 'aggregation' in error_str or 'data' in error_str:
            return 'data_aggregation'
        elif 'chart' in error_str:
            return 'chart_generation'
        elif 'report' in error_str or 'pdf' in error_str or 'excel' in error_str:
            return 'report_generation'
        else:
            return 'unknown'
    
    async def get_processing_metrics(self, template_id: Optional[int] = None, hours: int = 24) -> Dict[str, Any]:
        """Get processing metrics for analysis"""
        
        from sqlalchemy import text
        
        try:
            # Query processing jobs from database
            where_clause = "WHERE created_at >= NOW() - INTERVAL '%s hours'" % hours
            if template_id:
                where_clause += f" AND template_id = {template_id}"
            
            query = f"""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
                    AVG(CASE WHEN status = 'completed' THEN 
                        EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000 
                    END) as avg_processing_time_ms,
                    MAX(CASE WHEN status = 'completed' THEN 
                        EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000 
                    END) as max_processing_time_ms
                FROM report_processing_jobs
                {where_clause}
            """
            
            result = self.db.execute(text(query))
            row = result.fetchone()
            
            if row:
                metrics = dict(zip(result.keys(), row))
                
                # Calculate success rate
                total = metrics['total_jobs'] or 1
                metrics['success_rate'] = round((metrics['completed_jobs'] or 0) / total * 100, 2)
                
                return metrics
            
            return {
                'total_jobs': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'success_rate': 0,
                'avg_processing_time_ms': 0,
                'max_processing_time_ms': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get processing metrics: {str(e)}")
            return {}
    
    async def optimize_template_performance(self, template_id: int) -> Dict[str, Any]:
        """Analyze and provide performance optimization recommendations"""
        
        try:
            template_config = await self._get_template_configuration(template_id)
            
            optimization_report = {
                'template_id': template_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_sources': {},
                'charts': {},
                'recommendations': [],
                'estimated_improvement': {}
            }
            
            # Analyze data sources
            config = template_config.get('configuration', {})
            data_sources = config.get('data_sources', [])
            charts = config.get('charts', [])
            
            optimization_report['data_sources'] = {
                'count': len(data_sources),
                'external_sources': len([ds for ds in data_sources if ds.get('endpoint', '').startswith('http')]),
                'database_sources': len([ds for ds in data_sources if ds.get('endpoint', '').startswith('db:')]),
                'api_sources': len([ds for ds in data_sources if ds.get('endpoint', '').startswith('/api/')])
            }
            
            # Analyze charts
            if charts:
                chart_analysis = await self.chart_service.optimize_chart_generation(charts)
                optimization_report['charts'] = chart_analysis
            
            # Generate recommendations
            if optimization_report['data_sources']['count'] > 5:
                optimization_report['recommendations'].append({
                    'type': 'data_sources',
                    'message': 'Consider consolidating data sources or implementing aggressive caching',
                    'impact': 'high'
                })
            
            if optimization_report['data_sources']['external_sources'] > 2:
                optimization_report['recommendations'].append({
                    'type': 'external_apis',
                    'message': 'Multiple external API calls detected - consider data source caching',
                    'impact': 'medium'
                })
            
            if len(charts) > 8:
                optimization_report['recommendations'].append({
                    'type': 'charts',
                    'message': 'Large number of charts may impact performance - consider chart optimization',
                    'impact': 'medium'
                })
            
            return optimization_report
            
        except Exception as e:
            logger.error(f"Performance optimization analysis failed for template {template_id}: {str(e)}")
            return {'error': str(e)}

# Factory function
def create_template_processing_service(db: Session, **services) -> TemplateProcessingService:
    """Create and configure template processing service"""
    return TemplateProcessingService(db=db, **services)