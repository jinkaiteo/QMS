# Enhanced Chart Service - Phase B Sprint 2 Day 2 Template Processing
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import asyncio
import logging
import json
from dataclasses import dataclass
from .chart_generator import ChartConfiguration, PDFChartGenerator, ExcelChartGenerator, ChartDataProcessor

logger = logging.getLogger(__name__)

@dataclass
class ChartGenerationResult:
    """Result of chart generation operation"""
    success: bool
    chart_id: str
    chart_type: str
    format: str  # 'pdf', 'excel', 'both'
    data_processed: Dict[str, Any]
    generation_time_ms: int
    file_path: Optional[str] = None
    excel_chart_ref: Optional[str] = None
    pdf_drawing: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class EnhancedChartService:
    """
    Enhanced chart service for Template Processing Pipeline
    Integrates with data aggregation and provides async chart generation
    """
    
    def __init__(self, cache_service=None):
        self.cache_service = cache_service
        self.pdf_generator = PDFChartGenerator()
        self.excel_generator = ExcelChartGenerator()
        self.data_processor = ChartDataProcessor()
        
    async def generate_chart(self, 
                           chart_type: str,
                           chart_data: Dict[str, Any],
                           chart_config: Dict[str, Any],
                           output_format: str = 'both') -> ChartGenerationResult:
        """
        Generate chart for template processing
        
        Args:
            chart_type: Type of chart (bar, line, pie, etc.)
            chart_data: Processed chart data
            chart_config: Chart configuration
            output_format: 'pdf', 'excel', or 'both'
            
        Returns:
            ChartGenerationResult with generation details
        """
        start_time = datetime.now()
        chart_id = chart_config.get('id', f"chart_{datetime.now().timestamp()}")
        
        try:
            logger.info(f"Generating {chart_type} chart {chart_id} in format: {output_format}")
            
            # Process and validate data
            processed_data = await self._process_chart_data(chart_data, chart_config)
            
            # Create chart configuration
            config = self._create_chart_configuration(chart_type, chart_config)
            
            result = ChartGenerationResult(
                success=True,
                chart_id=chart_id,
                chart_type=chart_type,
                format=output_format,
                data_processed=processed_data,
                generation_time_ms=0,
                metadata={
                    'config': chart_config,
                    'data_points': len(processed_data.get('labels', [])),
                    'generation_timestamp': datetime.now().isoformat()
                }
            )
            
            # Generate charts based on format
            if output_format in ['pdf', 'both']:
                result.pdf_drawing = await self._generate_pdf_chart(config, processed_data)
            
            if output_format in ['excel', 'both']:
                result.excel_chart_ref = await self._generate_excel_chart_config(config, processed_data)
            
            # Calculate generation time
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result.generation_time_ms = generation_time
            
            logger.info(f"Chart {chart_id} generated successfully in {generation_time}ms")
            
            return result
            
        except Exception as e:
            generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Chart generation failed for {chart_id}: {str(e)}")
            
            return ChartGenerationResult(
                success=False,
                chart_id=chart_id,
                chart_type=chart_type,
                format=output_format,
                data_processed={},
                generation_time_ms=generation_time,
                error_message=str(e)
            )
    
    async def generate_multiple_charts(self, 
                                     charts_config: List[Dict[str, Any]],
                                     aggregated_data: Dict[str, Any]) -> List[ChartGenerationResult]:
        """
        Generate multiple charts concurrently
        
        Args:
            charts_config: List of chart configurations
            aggregated_data: Data from aggregation service
            
        Returns:
            List of chart generation results
        """
        logger.info(f"Generating {len(charts_config)} charts concurrently")
        
        # Create tasks for concurrent generation
        tasks = []
        for chart_config in charts_config:
            chart_type = chart_config.get('type', 'bar')
            data_source = chart_config.get('data_source')
            
            # Extract data for this chart
            chart_data = self._extract_chart_data(aggregated_data, data_source, chart_config)
            
            # Create generation task
            task = self.generate_chart(
                chart_type=chart_type,
                chart_data=chart_data,
                chart_config=chart_config,
                output_format=chart_config.get('output_format', 'both')
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = ChartGenerationResult(
                    success=False,
                    chart_id=f"chart_{i}",
                    chart_type=charts_config[i].get('type', 'unknown'),
                    format='unknown',
                    data_processed={},
                    generation_time_ms=0,
                    error_message=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        successful_charts = len([r for r in processed_results if r.success])
        logger.info(f"Chart generation completed: {successful_charts}/{len(charts_config)} successful")
        
        return processed_results
    
    async def _process_chart_data(self, chart_data: Dict[str, Any], chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw chart data for generation"""
        
        # Use existing data processor
        validation_result = self.data_processor.validate_chart_data(chart_data)
        if not validation_result[0]:
            raise ValueError(f"Chart data validation failed: {validation_result[1]}")
        
        # Extract fields
        x_field = chart_config.get('x_field', 'x')
        y_field = chart_config.get('y_field', 'y')
        
        # Process data based on structure
        if 'data' in chart_data and isinstance(chart_data['data'], list):
            data_list = chart_data['data']
        elif isinstance(chart_data, list):
            data_list = chart_data
        else:
            raise ValueError("Invalid chart data structure")
        
        processed = {
            'labels': [],
            'values': [],
            'datasets': []
        }
        
        # Extract values
        for item in data_list:
            if isinstance(item, dict):
                x_val = item.get(x_field, '')
                y_val = item.get(y_field, 0)
                
                processed['labels'].append(str(x_val))
                processed['values'].append(float(y_val) if isinstance(y_val, (int, float)) else 0)
        
        # Create dataset for chart generators
        processed['datasets'] = [{
            'label': chart_config.get('title', 'Data'),
            'data': processed['values']
        }]
        
        return processed
    
    def _extract_chart_data(self, aggregated_data: Dict[str, Any], data_source: str, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract chart-specific data from aggregated data"""
        
        if not data_source:
            raise ValueError("Chart data source not specified")
        
        # Look for data source in aggregated data
        raw_data = aggregated_data.get('raw_data', {})
        
        if data_source not in raw_data:
            raise ValueError(f"Data source '{data_source}' not found in aggregated data")
        
        source_data = raw_data[data_source]
        
        # Handle different data formats
        if isinstance(source_data, dict):
            if 'data' in source_data:
                return source_data
            elif 'programs' in source_data:  # Training data format
                return {'data': source_data['programs']}
            elif 'events' in source_data:  # Quality events format
                return {'data': source_data['events']}
            elif 'documents' in source_data:  # Document data format
                return {'data': source_data['documents']}
            elif 'users' in source_data:  # User data format
                return {'data': source_data['users']}
            else:
                # Try to use the data as-is
                return {'data': [source_data]}
        elif isinstance(source_data, list):
            return {'data': source_data}
        else:
            raise ValueError(f"Unsupported data format for source '{data_source}'")
    
    def _create_chart_configuration(self, chart_type: str, chart_config: Dict[str, Any]) -> ChartConfiguration:
        """Create ChartConfiguration object from config dict"""
        
        return ChartConfiguration(
            chart_type=chart_type,
            title=chart_config.get('title', 'Chart'),
            width=chart_config.get('width', 400),
            height=chart_config.get('height', 300),
            x_axis_title=chart_config.get('x_axis_title', chart_config.get('x_label', '')),
            y_axis_title=chart_config.get('y_axis_title', chart_config.get('y_label', '')),
            colors=chart_config.get('colors'),
            show_legend=chart_config.get('show_legend', True),
            show_values=chart_config.get('show_values', False)
        )
    
    async def _generate_pdf_chart(self, config: ChartConfiguration, processed_data: Dict[str, Any]) -> Any:
        """Generate PDF chart drawing"""
        
        try:
            # Convert processed data to format expected by PDF generator
            pdf_data = {
                'labels': processed_data['labels'],
                'datasets': processed_data['datasets']
            }
            
            # Generate chart
            drawing = self.pdf_generator.generate_chart(config, pdf_data)
            
            return drawing
            
        except Exception as e:
            logger.error(f"PDF chart generation failed: {str(e)}")
            raise e
    
    async def _generate_excel_chart_config(self, config: ChartConfiguration, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Excel chart configuration"""
        
        try:
            # Create Excel chart configuration that can be used by Excel generator
            excel_config = {
                'type': config.chart_type,
                'title': config.title,
                'width': config.width,
                'height': config.height,
                'x_axis_title': config.x_axis_title,
                'y_axis_title': config.y_axis_title,
                'show_legend': config.show_legend,
                'data': {
                    'labels': processed_data['labels'],
                    'values': processed_data['values']
                },
                'style': {
                    'colors': config.colors,
                    'show_values': config.show_values
                }
            }
            
            return excel_config
            
        except Exception as e:
            logger.error(f"Excel chart configuration failed: {str(e)}")
            raise e
    
    async def generate_chart_for_template(self, 
                                        template_id: int,
                                        chart_config: Dict[str, Any],
                                        aggregated_data: Dict[str, Any]) -> ChartGenerationResult:
        """
        Generate chart specifically for template processing
        Includes caching and optimization for template workflows
        """
        
        # Generate cache key
        cache_key = self._generate_chart_cache_key(template_id, chart_config, aggregated_data)
        
        # Check cache
        if self.cache_service:
            cached_result = await self.cache_service.get_async(cache_key)
            if cached_result:
                logger.debug(f"Chart cache hit for template {template_id}")
                return cached_result
        
        # Generate chart
        chart_type = chart_config.get('type', 'bar')
        data_source = chart_config.get('data_source')
        
        chart_data = self._extract_chart_data(aggregated_data, data_source, chart_config)
        
        result = await self.generate_chart(
            chart_type=chart_type,
            chart_data=chart_data,
            chart_config=chart_config,
            output_format=chart_config.get('output_format', 'both')
        )
        
        # Cache successful results
        if self.cache_service and result.success:
            cache_ttl = chart_config.get('cache_ttl', 1800)  # 30 minutes default
            await self.cache_service.set_async(cache_key, result, ttl=cache_ttl)
        
        return result
    
    def _generate_chart_cache_key(self, template_id: int, chart_config: Dict[str, Any], aggregated_data: Dict[str, Any]) -> str:
        """Generate cache key for chart"""
        
        import hashlib
        
        # Create cache key from template, config, and data hash
        key_data = {
            'template_id': template_id,
            'chart_config': chart_config,
            'data_hash': hashlib.md5(json.dumps(aggregated_data, sort_keys=True, default=str).encode()).hexdigest()[:8]
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"chart:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def optimize_chart_generation(self, charts_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze and optimize chart generation configuration
        """
        
        optimization_report = {
            'total_charts': len(charts_config),
            'chart_types': {},
            'data_sources': set(),
            'recommendations': []
        }
        
        # Analyze chart configurations
        for chart_config in charts_config:
            chart_type = chart_config.get('type', 'unknown')
            data_source = chart_config.get('data_source')
            
            # Count chart types
            optimization_report['chart_types'][chart_type] = optimization_report['chart_types'].get(chart_type, 0) + 1
            
            # Track data sources
            if data_source:
                optimization_report['data_sources'].add(data_source)
        
        optimization_report['data_sources'] = list(optimization_report['data_sources'])
        optimization_report['unique_data_sources'] = len(optimization_report['data_sources'])
        
        # Generate recommendations
        if optimization_report['total_charts'] > 10:
            optimization_report['recommendations'].append("Consider concurrent chart generation for better performance")
        
        if optimization_report['unique_data_sources'] > 5:
            optimization_report['recommendations'].append("Multiple data sources detected - ensure proper caching is configured")
        
        if 'pie' in optimization_report['chart_types'] and optimization_report['chart_types']['pie'] > 3:
            optimization_report['recommendations'].append("Multiple pie charts detected - consider consolidating data or using alternative visualization")
        
        return optimization_report

# Factory function
def create_enhanced_chart_service(cache_service=None) -> EnhancedChartService:
    """Create and configure enhanced chart service"""
    return EnhancedChartService(cache_service=cache_service)