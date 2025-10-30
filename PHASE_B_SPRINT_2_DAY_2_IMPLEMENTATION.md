# 🔄 Phase B Sprint 2 Day 2 - Template Processing Pipeline

**Phase**: B - Advanced Reporting & Analytics  
**Sprint**: 2 - Report Generation & Compliance  
**Day**: 2 - Template Processing Pipeline & Data Aggregation  
**Focus**: Advanced data processing, chart generation, and performance optimization

---

## 🎯 **Day 2 Objectives**

### **Primary Goals:**
- [ ] Build intelligent data aggregation pipeline from multiple sources
- [ ] Implement PDF chart generation with ReportLab graphics
- [ ] Create Excel chart integration with OpenPyXL
- [ ] Develop template validation and testing framework
- [ ] Add performance optimization with intelligent caching
- [ ] Build report processing workflow orchestrator

### **Deliverables:**
- Multi-source data aggregation service
- PDF chart generation with professional styling
- Excel chart integration with native Excel charts
- Template validation framework with error handling
- Performance caching system with intelligent invalidation
- Report processing orchestrator with monitoring

---

## 🏗️ **Building on Day 1 Foundation**

### **Existing Infrastructure:**
- ✅ **Database Schema**: 4 core tables with enterprise features
- ✅ **PDF Generator**: Professional ReportLab service with styling
- ✅ **Excel Generator**: Multi-sheet OpenPyXL with formatting
- ✅ **Template System**: Dynamic parameterized configurations
- ✅ **Background Queue**: Priority-based processing system

### **Day 2 Enhancements:**
- 🔜 **Data Aggregation Pipeline**: Smart multi-source data collection
- 🔜 **Chart Generation**: Professional charts for PDF and Excel
- 🔜 **Template Validation**: Advanced testing and error recovery
- 🔜 **Performance Caching**: Intelligent data and chart caching
- 🔜 **Processing Orchestrator**: Workflow management and monitoring

---

## 📊 **Data Aggregation Pipeline**

### **Multi-Source Data Collection Service**

#### **Data Aggregation Engine**
```python
# backend/app/services/reporting/data_aggregator.py
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
import json
import hashlib
from dataclasses import dataclass

@dataclass
class DataSource:
    """Configuration for a data source"""
    name: str
    endpoint: str
    method: str = 'GET'
    headers: Dict[str, str] = None
    params: Dict[str, Any] = None
    timeout: int = 30
    cache_ttl: int = 300  # 5 minutes default
    retry_count: int = 3
    required: bool = True

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
    
    def __init__(self, cache_service=None):
        self.cache_service = cache_service
        self.base_url = "http://localhost:8001"  # Analytics backend
        
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
            # Process data sources concurrently
            async with aiohttp.ClientSession() as session:
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
                            
                    except Exception as e:
                        source = next(s for s in data_sources if s.name == source_name)
                        if source.required:
                            errors.append(f"Required source '{source_name}' failed: {str(e)}")
                        sources_failed.append(source_name)
            
            # Post-process collected data
            processed_data = await self._post_process_data(collected_data, parameters)
            
            # Calculate collection time
            collection_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
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
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                return cached_data, True
        
        # Prepare request
        url = f"{self.base_url}{source.endpoint}"
        headers = source.headers or {}
        params = {**(source.params or {}), **parameters}
        
        # Make request with retries
        for attempt in range(source.retry_count):
            try:
                async with session.request(
                    source.method,
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=source.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache successful response
                        if self.cache_service:
                            await self.cache_service.set(
                                cache_key, data, ttl=source.cache_ttl
                            )
                        
                        return data, False
                    else:
                        error_msg = f"HTTP {response.status} from {source.name}"
                        if attempt == source.retry_count - 1:
                            raise Exception(error_msg)
                        
            except asyncio.TimeoutError:
                error_msg = f"Timeout collecting from {source.name}"
                if attempt == source.retry_count - 1:
                    raise Exception(error_msg)
            except Exception as e:
                if attempt == source.retry_count - 1:
                    raise e
                
            # Wait before retry (exponential backoff)
            await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"Failed to collect from {source.name} after {source.retry_count} attempts")
    
    def _generate_cache_key(self, 
                           source: DataSource, 
                           parameters: Dict[str, Any],
                           template_id: Optional[int] = None) -> str:
        """Generate cache key for data source request"""
        key_data = {
            'source': source.name,
            'endpoint': source.endpoint,
            'params': sorted((source.params or {}).items()),
            'parameters': sorted(parameters.items()),
            'template_id': template_id
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return f"data_agg:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def _post_process_data(self, 
                                collected_data: Dict[str, Any], 
                                parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process collected data for report generation"""
        
        processed_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'parameters': parameters,
                'collection_timestamp': datetime.now().isoformat()
            }
        }
        
        # Process each data source
        for source_name, source_data in collected_data.items():
            if source_name == 'quality_metrics':
                processed_data.update(self._process_quality_data(source_data))
            elif source_name == 'training_metrics':
                processed_data.update(self._process_training_data(source_data))
            elif source_name == 'document_metrics':
                processed_data.update(self._process_document_data(source_data))
            elif source_name == 'department_data':
                processed_data.update(self._process_department_data(source_data))
            else:
                # Generic processing
                processed_data[source_name] = source_data
        
        # Generate summary statistics
        processed_data['summary'] = self._generate_summary(processed_data)
        
        return processed_data
    
    def _process_quality_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process quality metrics data"""
        quality_data = data.get('data', {}) if 'data' in data else data
        
        return {
            'quality_metrics': quality_data,
            'kpis': self._extract_quality_kpis(quality_data),
            'quality_trends': self._extract_quality_trends(quality_data)
        }
    
    def _process_training_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process training metrics data"""
        training_data = data.get('data', {}) if 'data' in data else data
        
        return {
            'training_metrics': training_data,
            'training_kpis': self._extract_training_kpis(training_data),
            'compliance_status': self._extract_compliance_status(training_data)
        }
    
    def _process_document_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process document metrics data"""
        document_data = data.get('data', {}) if 'data' in data else data
        
        return {
            'document_metrics': document_data,
            'document_kpis': self._extract_document_kpis(document_data),
            'workflow_analysis': self._extract_workflow_analysis(document_data)
        }
    
    def _process_department_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process department analytics data"""
        dept_data = data.get('data', {}) if 'data' in data else data
        
        return {
            'departments': self._format_department_data(dept_data),
            'department_comparison': self._generate_department_comparison(dept_data)
        }
    
    def _extract_quality_kpis(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract KPIs from quality data"""
        metrics = data.get('metrics', {})
        kpis = []
        
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict) and 'average' in metric_data:
                kpi = {
                    'name': metric_name.replace('_', ' ').title(),
                    'value': round(metric_data['average'], 1),
                    'unit': self._determine_unit(metric_name),
                    'trend': self._calculate_trend(metric_data),
                    'status': self._determine_status(metric_data['average'], metric_name)
                }
                kpis.append(kpi)
        
        return kpis[:6]  # Limit to top 6 KPIs
    
    def _extract_training_kpis(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract KPIs from training data"""
        kpis = []
        
        if 'completion_rate' in data:
            kpis.append({
                'name': 'Training Completion Rate',
                'value': round(data['completion_rate'], 1),
                'unit': '%',
                'trend': 'up' if data['completion_rate'] > 85 else 'down',
                'status': 'excellent' if data['completion_rate'] > 90 else 'good'
            })
        
        if 'overdue_count' in data:
            kpis.append({
                'name': 'Overdue Training Items',
                'value': data['overdue_count'],
                'unit': 'items',
                'trend': 'down' if data['overdue_count'] < 20 else 'up',
                'status': 'excellent' if data['overdue_count'] < 10 else 'warning'
            })
        
        return kpis
    
    def _extract_document_kpis(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract KPIs from document data"""
        kpis = []
        
        if 'documents_created' in data:
            kpis.append({
                'name': 'Documents Created',
                'value': data['documents_created'],
                'unit': 'docs',
                'trend': 'up',
                'status': 'good'
            })
        
        if 'average_approval_time' in data:
            kpis.append({
                'name': 'Avg Approval Time',
                'value': round(data['average_approval_time'], 1),
                'unit': 'days',
                'trend': 'down' if data['average_approval_time'] < 3 else 'up',
                'status': 'excellent' if data['average_approval_time'] < 2 else 'good'
            })
        
        return kpis
    
    def _determine_unit(self, metric_name: str) -> str:
        """Determine appropriate unit for a metric"""
        if 'percentage' in metric_name.lower() or 'rate' in metric_name.lower():
            return '%'
        elif 'time' in metric_name.lower():
            return 'days'
        elif 'count' in metric_name.lower():
            return 'items'
        else:
            return ''
    
    def _calculate_trend(self, metric_data: Dict[str, Any]) -> str:
        """Calculate trend direction from metric data"""
        current = metric_data.get('average', 0)
        previous = metric_data.get('previous_average', current)
        
        if current > previous * 1.05:
            return 'up'
        elif current < previous * 0.95:
            return 'down'
        else:
            return 'flat'
    
    def _determine_status(self, value: float, metric_name: str) -> str:
        """Determine status color based on value and metric type"""
        if 'quality' in metric_name.lower() or 'compliance' in metric_name.lower():
            if value >= 95:
                return 'excellent'
            elif value >= 85:
                return 'good'
            elif value >= 70:
                return 'warning'
            else:
                return 'critical'
        else:
            return 'good'
    
    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from processed data"""
        summary = {
            'total_kpis': 0,
            'quality_score': 0,
            'training_compliance': 0,
            'document_efficiency': 0,
            'overall_status': 'good'
        }
        
        # Count KPIs
        all_kpis = []
        for key in ['kpis', 'training_kpis', 'document_kpis']:
            if key in data:
                all_kpis.extend(data[key])
        
        summary['total_kpis'] = len(all_kpis)
        
        # Calculate averages
        if 'quality_metrics' in data:
            summary['quality_score'] = self._calculate_average_score(data['quality_metrics'])
        
        if 'training_metrics' in data:
            summary['training_compliance'] = data['training_metrics'].get('completion_rate', 0)
        
        if 'document_metrics' in data:
            summary['document_efficiency'] = 100 - min(data['document_metrics'].get('average_approval_time', 5) * 10, 100)
        
        # Determine overall status
        scores = [summary['quality_score'], summary['training_compliance'], summary['document_efficiency']]
        avg_score = sum(s for s in scores if s > 0) / len([s for s in scores if s > 0]) if any(s > 0 for s in scores) else 0
        
        if avg_score >= 90:
            summary['overall_status'] = 'excellent'
        elif avg_score >= 75:
            summary['overall_status'] = 'good'
        elif avg_score >= 60:
            summary['overall_status'] = 'warning'
        else:
            summary['overall_status'] = 'critical'
        
        return summary
    
    def _calculate_average_score(self, quality_data: Dict[str, Any]) -> float:
        """Calculate average quality score from metrics"""
        metrics = quality_data.get('metrics', {})
        if not metrics:
            return 0
        
        scores = []
        for metric_data in metrics.values():
            if isinstance(metric_data, dict) and 'average' in metric_data:
                scores.append(metric_data['average'])
        
        return sum(scores) / len(scores) if scores else 0
```

Let me continue with the chart generation and caching systems...