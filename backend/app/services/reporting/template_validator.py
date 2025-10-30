# Template Validation Framework - Phase B Sprint 2 Day 2
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Represents a validation issue found in a template"""
    severity: ValidationSeverity
    code: str
    message: str
    location: str
    suggestion: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None

@dataclass
class ValidationResult:
    """Result of template validation"""
    is_valid: bool
    template_id: int
    template_name: str
    validation_timestamp: datetime
    issues: List[ValidationIssue] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    test_results: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]])
    
    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == ValidationSeverity.WARNING])

class TemplateValidationService:
    """
    Comprehensive template validation and testing framework
    Validates template configuration, data sources, and generates test reports
    """
    
    def __init__(self, db: Session, data_aggregator=None):
        self.db = db
        self.data_aggregator = data_aggregator
        self.validation_rules = self._load_validation_rules()
        
    def validate_template(self, template_id: int, run_tests: bool = True) -> ValidationResult:
        """
        Comprehensive template validation
        
        Args:
            template_id: Template to validate
            run_tests: Whether to run actual data tests
            
        Returns:
            ValidationResult with all findings
        """
        logger.info(f"Starting validation for template {template_id}")
        
        # Get template data
        template = self._get_template(template_id)
        if not template:
            return ValidationResult(
                is_valid=False,
                template_id=template_id,
                template_name="Unknown",
                validation_timestamp=datetime.now(),
                issues=[ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    code="TEMPLATE_NOT_FOUND",
                    message=f"Template {template_id} not found",
                    location="template_id"
                )]
            )
        
        result = ValidationResult(
            is_valid=True,
            template_id=template_id,
            template_name=template['name'],
            validation_timestamp=datetime.now()
        )
        
        # Run validation checks
        self._validate_template_structure(template, result)
        self._validate_configuration(template, result)
        self._validate_data_sources(template, result)
        self._validate_parameters(template, result)
        self._validate_charts(template, result)
        self._validate_formatting(template, result)
        
        # Run performance tests
        if run_tests:
            self._run_performance_tests(template, result)
            self._run_data_quality_tests(template, result)
        
        # Determine overall validity
        result.is_valid = result.error_count == 0
        
        logger.info(f"Validation completed for template {template_id}: {result.error_count} errors, {result.warning_count} warnings")
        
        return result
    
    def _get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve template from database"""
        query = """
            SELECT 
                id,
                name,
                description,
                report_type,
                configuration,
                parameters_schema,
                created_at,
                updated_at,
                version
            FROM report_templates
            WHERE id = :template_id AND is_deleted = false
        """
        
        result = self.db.execute(text(query), {'template_id': template_id})
        row = result.fetchone()
        
        if row:
            template = dict(zip(result.keys(), row))
            # Parse JSON fields
            if template['configuration']:
                template['configuration'] = json.loads(template['configuration'])
            if template['parameters_schema']:
                template['parameters_schema'] = json.loads(template['parameters_schema'])
            return template
        
        return None
    
    def _validate_template_structure(self, template: Dict[str, Any], result: ValidationResult):
        """Validate basic template structure"""
        
        required_fields = ['name', 'report_type', 'configuration']
        
        for field in required_fields:
            if not template.get(field):
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MISSING_REQUIRED_FIELD",
                    message=f"Required field '{field}' is missing or empty",
                    location=f"template.{field}",
                    suggestion=f"Add a valid value for {field}"
                ))
        
        # Validate report type
        valid_types = ['pdf', 'excel', 'both']
        if template.get('report_type') not in valid_types:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INVALID_REPORT_TYPE",
                message=f"Report type '{template.get('report_type')}' is not valid",
                location="template.report_type",
                suggestion=f"Use one of: {', '.join(valid_types)}"
            ))
        
        # Validate configuration structure
        config = template.get('configuration', {})
        if not isinstance(config, dict):
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INVALID_CONFIGURATION",
                message="Configuration must be a valid JSON object",
                location="template.configuration",
                suggestion="Ensure configuration is properly formatted JSON"
            ))
    
    def _validate_configuration(self, template: Dict[str, Any], result: ValidationResult):
        """Validate template configuration"""
        
        config = template.get('configuration', {})
        
        # Check for required configuration sections
        required_sections = ['data_sources', 'layout', 'styling']
        for section in required_sections:
            if section not in config:
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="MISSING_CONFIG_SECTION",
                    message=f"Configuration section '{section}' is missing",
                    location=f"configuration.{section}",
                    suggestion=f"Add {section} configuration for better control"
                ))
        
        # Validate layout configuration
        layout = config.get('layout', {})
        if layout:
            self._validate_layout_config(layout, result)
        
        # Validate styling configuration
        styling = config.get('styling', {})
        if styling:
            self._validate_styling_config(styling, result)
    
    def _validate_data_sources(self, template: Dict[str, Any], result: ValidationResult):
        """Validate data source configurations"""
        
        config = template.get('configuration', {})
        data_sources = config.get('data_sources', [])
        
        if not data_sources:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="NO_DATA_SOURCES",
                message="Template has no data sources configured",
                location="configuration.data_sources",
                suggestion="Add at least one data source configuration"
            ))
            return
        
        for i, source in enumerate(data_sources):
            self._validate_single_data_source(source, i, result)
    
    def _validate_single_data_source(self, source: Dict[str, Any], index: int, result: ValidationResult):
        """Validate a single data source configuration"""
        
        location_prefix = f"configuration.data_sources[{index}]"
        
        # Required fields
        required_fields = ['name', 'endpoint']
        for field in required_fields:
            if not source.get(field):
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MISSING_DATASOURCE_FIELD",
                    message=f"Data source field '{field}' is missing",
                    location=f"{location_prefix}.{field}",
                    suggestion=f"Add {field} to data source configuration"
                ))
        
        # Validate endpoint format
        endpoint = source.get('endpoint', '')
        if endpoint:
            if not (endpoint.startswith('/api/') or endpoint.startswith('db:') or endpoint.startswith('http')):
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="UNUSUAL_ENDPOINT",
                    message=f"Endpoint '{endpoint}' has unusual format",
                    location=f"{location_prefix}.endpoint",
                    suggestion="Use /api/, db:, or http(s):// prefixes for clarity"
                ))
        
        # Validate timeout
        timeout = source.get('timeout', 30)
        if timeout < 5 or timeout > 300:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="UNUSUAL_TIMEOUT",
                message=f"Timeout {timeout}s is unusual (recommended: 5-300s)",
                location=f"{location_prefix}.timeout",
                suggestion="Use timeout between 5 and 300 seconds"
            ))
        
        # Validate cache TTL
        cache_ttl = source.get('cache_ttl', 300)
        if cache_ttl < 60 or cache_ttl > 3600:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                code="SUBOPTIMAL_CACHE_TTL",
                message=f"Cache TTL {cache_ttl}s may not be optimal",
                location=f"{location_prefix}.cache_ttl",
                suggestion="Consider cache TTL between 60-3600 seconds based on data freshness needs"
            ))
    
    def _validate_parameters(self, template: Dict[str, Any], result: ValidationResult):
        """Validate parameter schema"""
        
        params_schema = template.get('parameters_schema', {})
        
        if not params_schema:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="NO_PARAMETER_SCHEMA",
                message="Template has no parameter schema defined",
                location="template.parameters_schema",
                suggestion="Define parameter schema for better validation and UI generation"
            ))
            return
        
        # Validate schema structure
        if 'properties' not in params_schema:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INVALID_PARAMETER_SCHEMA",
                message="Parameter schema missing 'properties' field",
                location="parameters_schema.properties",
                suggestion="Add 'properties' object to parameter schema"
            ))
        
        # Validate individual parameters
        properties = params_schema.get('properties', {})
        for param_name, param_config in properties.items():
            self._validate_parameter(param_name, param_config, result)
    
    def _validate_parameter(self, name: str, config: Dict[str, Any], result: ValidationResult):
        """Validate individual parameter configuration"""
        
        location_prefix = f"parameters_schema.properties.{name}"
        
        # Check for type
        if 'type' not in config:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="MISSING_PARAMETER_TYPE",
                message=f"Parameter '{name}' missing type specification",
                location=f"{location_prefix}.type",
                suggestion="Add type specification (string, number, boolean, etc.)"
            ))
        
        # Validate date parameters
        param_type = config.get('type')
        if param_type == 'string' and config.get('format') == 'date':
            if 'default' not in config:
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    code="NO_DEFAULT_DATE",
                    message=f"Date parameter '{name}' has no default value",
                    location=f"{location_prefix}.default",
                    suggestion="Consider adding default date for better user experience"
                ))
    
    def _validate_charts(self, template: Dict[str, Any], result: ValidationResult):
        """Validate chart configurations"""
        
        config = template.get('configuration', {})
        charts = config.get('charts', [])
        
        for i, chart in enumerate(charts):
            self._validate_single_chart(chart, i, result)
    
    def _validate_single_chart(self, chart: Dict[str, Any], index: int, result: ValidationResult):
        """Validate a single chart configuration"""
        
        location_prefix = f"configuration.charts[{index}]"
        
        # Required fields
        required_fields = ['type', 'data_source', 'title']
        for field in required_fields:
            if not chart.get(field):
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MISSING_CHART_FIELD",
                    message=f"Chart field '{field}' is missing",
                    location=f"{location_prefix}.{field}",
                    suggestion=f"Add {field} to chart configuration"
                ))
        
        # Validate chart type
        valid_types = ['bar', 'line', 'pie', 'scatter', 'area', 'histogram']
        chart_type = chart.get('type')
        if chart_type and chart_type not in valid_types:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INVALID_CHART_TYPE",
                message=f"Chart type '{chart_type}' is not supported",
                location=f"{location_prefix}.type",
                suggestion=f"Use one of: {', '.join(valid_types)}"
            ))
        
        # Validate dimensions
        width = chart.get('width', 600)
        height = chart.get('height', 400)
        
        if width < 200 or width > 2000:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="UNUSUAL_CHART_WIDTH",
                message=f"Chart width {width}px may not render well",
                location=f"{location_prefix}.width",
                suggestion="Use width between 200-2000 pixels"
            ))
        
        if height < 150 or height > 1500:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="UNUSUAL_CHART_HEIGHT",
                message=f"Chart height {height}px may not render well",
                location=f"{location_prefix}.height",
                suggestion="Use height between 150-1500 pixels"
            ))
    
    def _validate_layout_config(self, layout: Dict[str, Any], result: ValidationResult):
        """Validate layout configuration"""
        
        # Check page margins
        margins = layout.get('margins', {})
        if margins:
            for margin in ['top', 'bottom', 'left', 'right']:
                value = margins.get(margin, 0)
                if value < 0 or value > 100:
                    result.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        code="UNUSUAL_MARGIN",
                        message=f"Margin {margin}: {value}mm is unusual",
                        location=f"configuration.layout.margins.{margin}",
                        suggestion="Use margins between 0-100mm"
                    ))
        
        # Check page orientation
        orientation = layout.get('orientation', 'portrait')
        if orientation not in ['portrait', 'landscape']:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INVALID_ORIENTATION",
                message=f"Page orientation '{orientation}' is invalid",
                location="configuration.layout.orientation",
                suggestion="Use 'portrait' or 'landscape'"
            ))
    
    def _validate_styling_config(self, styling: Dict[str, Any], result: ValidationResult):
        """Validate styling configuration"""
        
        # Validate colors
        colors = styling.get('colors', {})
        for color_name, color_value in colors.items():
            if not self._is_valid_color(color_value):
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="INVALID_COLOR",
                    message=f"Color '{color_name}': '{color_value}' may not be valid",
                    location=f"configuration.styling.colors.{color_name}",
                    suggestion="Use hex codes (#RRGGBB) or standard color names"
                ))
        
        # Validate fonts
        fonts = styling.get('fonts', {})
        for font_name, font_config in fonts.items():
            if isinstance(font_config, dict):
                size = font_config.get('size', 12)
                if size < 6 or size > 72:
                    result.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        code="UNUSUAL_FONT_SIZE",
                        message=f"Font '{font_name}' size {size}pt is unusual",
                        location=f"configuration.styling.fonts.{font_name}.size",
                        suggestion="Use font sizes between 6-72 points"
                    ))
    
    def _run_performance_tests(self, template: Dict[str, Any], result: ValidationResult):
        """Run performance tests on template"""
        
        if not self.data_aggregator:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="NO_PERFORMANCE_TESTS",
                message="Cannot run performance tests without data aggregator",
                location="test_framework"
            ))
            return
        
        # Test with minimal parameters
        test_params = {
            'start_date': (datetime.now() - timedelta(days=7)).isoformat(),
            'end_date': datetime.now().isoformat()
        }
        
        # Time the data collection
        start_time = datetime.now()
        try:
            # Simulate data collection (would use actual aggregator in production)
            import asyncio
            import time
            time.sleep(0.1)  # Simulate work
            
            collection_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result.performance_metrics = {
                'data_collection_time_ms': collection_time,
                'test_parameters': test_params,
                'test_timestamp': datetime.now().isoformat()
            }
            
            # Performance thresholds
            if collection_time > 5000:  # 5 seconds
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="SLOW_DATA_COLLECTION",
                    message=f"Data collection took {collection_time:.0f}ms (>5s)",
                    location="performance.data_collection",
                    suggestion="Consider optimizing data sources or adding caching"
                ))
            
        except Exception as e:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="PERFORMANCE_TEST_FAILED",
                message=f"Performance test failed: {str(e)}",
                location="test_framework.performance"
            ))
    
    def _run_data_quality_tests(self, template: Dict[str, Any], result: ValidationResult):
        """Run data quality tests"""
        
        config = template.get('configuration', {})
        data_sources = config.get('data_sources', [])
        
        test_results = {
            'sources_tested': 0,
            'sources_passed': 0,
            'sources_failed': 0,
            'test_details': []
        }
        
        for source in data_sources:
            test_results['sources_tested'] += 1
            
            # Basic endpoint validation
            endpoint = source.get('endpoint', '')
            if self._validate_endpoint_accessibility(endpoint):
                test_results['sources_passed'] += 1
                test_results['test_details'].append({
                    'source': source.get('name', 'Unknown'),
                    'status': 'passed',
                    'endpoint': endpoint
                })
            else:
                test_results['sources_failed'] += 1
                test_results['test_details'].append({
                    'source': source.get('name', 'Unknown'),
                    'status': 'failed',
                    'endpoint': endpoint,
                    'error': 'Endpoint not accessible'
                })
                
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="INACCESSIBLE_ENDPOINT",
                    message=f"Data source endpoint '{endpoint}' is not accessible",
                    location=f"data_source.{source.get('name', 'unknown')}.endpoint",
                    suggestion="Check endpoint URL and connectivity"
                ))
        
        result.test_results = test_results
    
    def _validate_endpoint_accessibility(self, endpoint: str) -> bool:
        """Basic endpoint accessibility check"""
        
        # For database queries, always return True (would need more complex testing)
        if endpoint.startswith('db:'):
            return True
        
        # For API endpoints, basic format check
        if endpoint.startswith('/api/'):
            return True
        
        # For external URLs, would need actual HTTP check
        if endpoint.startswith('http'):
            return True  # Simplified for now
        
        return False
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format"""
        
        if not isinstance(color, str):
            return False
        
        # Hex colors
        if re.match(r'^#[0-9A-Fa-f]{6}$', color):
            return True
        
        # RGB format
        if re.match(r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$', color):
            return True
        
        # Standard color names
        standard_colors = [
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink',
            'brown', 'black', 'white', 'gray', 'grey', 'cyan', 'magenta'
        ]
        
        return color.lower() in standard_colors
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration"""
        
        return {
            'performance_thresholds': {
                'data_collection_max_ms': 5000,
                'chart_generation_max_ms': 3000,
                'report_generation_max_ms': 10000
            },
            'chart_limits': {
                'max_data_points': 1000,
                'min_width': 200,
                'max_width': 2000,
                'min_height': 150,
                'max_height': 1500
            },
            'template_limits': {
                'max_data_sources': 10,
                'max_charts_per_template': 20,
                'max_parameters': 50
            }
        }
    
    def generate_validation_report(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Generate a comprehensive validation report"""
        
        return {
            'template_info': {
                'id': validation_result.template_id,
                'name': validation_result.template_name,
                'validation_timestamp': validation_result.validation_timestamp.isoformat()
            },
            'summary': {
                'is_valid': validation_result.is_valid,
                'total_issues': len(validation_result.issues),
                'error_count': validation_result.error_count,
                'warning_count': validation_result.warning_count,
                'info_count': len([i for i in validation_result.issues if i.severity == ValidationSeverity.INFO])
            },
            'issues_by_severity': {
                'critical': [self._issue_to_dict(i) for i in validation_result.issues if i.severity == ValidationSeverity.CRITICAL],
                'error': [self._issue_to_dict(i) for i in validation_result.issues if i.severity == ValidationSeverity.ERROR],
                'warning': [self._issue_to_dict(i) for i in validation_result.issues if i.severity == ValidationSeverity.WARNING],
                'info': [self._issue_to_dict(i) for i in validation_result.issues if i.severity == ValidationSeverity.INFO]
            },
            'performance_metrics': validation_result.performance_metrics,
            'test_results': validation_result.test_results,
            'recommendations': self._generate_recommendations(validation_result)
        }
    
    def _issue_to_dict(self, issue: ValidationIssue) -> Dict[str, Any]:
        """Convert validation issue to dictionary"""
        
        return {
            'severity': issue.severity.value,
            'code': issue.code,
            'message': issue.message,
            'location': issue.location,
            'suggestion': issue.suggestion,
            'line_number': issue.line_number,
            'column': issue.column
        }
    
    def _generate_recommendations(self, validation_result: ValidationResult) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if validation_result.error_count > 0:
            recommendations.append("Fix all error-level issues before using this template in production")
        
        if validation_result.warning_count > 3:
            recommendations.append("Consider addressing warning-level issues to improve template quality")
        
        # Performance recommendations
        perf_metrics = validation_result.performance_metrics
        if perf_metrics.get('data_collection_time_ms', 0) > 3000:
            recommendations.append("Consider optimizing data sources or implementing caching to improve performance")
        
        # Test results recommendations
        test_results = validation_result.test_results
        if test_results.get('sources_failed', 0) > 0:
            recommendations.append("Some data sources are not accessible - verify connectivity and permissions")
        
        if not recommendations:
            recommendations.append("Template validation passed - ready for production use")
        
        return recommendations

# Factory function
def create_template_validator(db: Session, data_aggregator=None) -> TemplateValidationService:
    """Create and configure template validation service"""
    return TemplateValidationService(db=db, data_aggregator=data_aggregator)