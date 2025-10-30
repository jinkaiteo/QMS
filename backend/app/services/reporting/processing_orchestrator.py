# Report Processing Orchestrator - Phase B Sprint 2 Day 2
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import asyncio
import json
import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text
import traceback

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Report processing status"""
    PENDING = "pending"
    VALIDATING = "validating"
    COLLECTING_DATA = "collecting_data"
    GENERATING_CHARTS = "generating_charts"
    RENDERING_REPORT = "rendering_report"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingPriority(Enum):
    """Processing priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class ProcessingStep:
    """Individual processing step"""
    name: str
    function: Callable
    required: bool = True
    timeout_seconds: int = 300
    retry_count: int = 3
    dependencies: List[str] = field(default_factory=list)

@dataclass
class ProcessingMetrics:
    """Processing performance metrics"""
    total_time_ms: int = 0
    validation_time_ms: int = 0
    data_collection_time_ms: int = 0
    chart_generation_time_ms: int = 0
    report_generation_time_ms: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    data_sources_processed: int = 0
    charts_generated: int = 0
    errors_encountered: int = 0

@dataclass
class ProcessingJob:
    """Report processing job"""
    job_id: str
    template_id: int
    parameters: Dict[str, Any]
    status: ProcessingStatus = ProcessingStatus.PENDING
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    current_step: str = ""
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    metrics: ProcessingMetrics = field(default_factory=ProcessingMetrics)
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)

class ReportProcessingOrchestrator:
    """
    Orchestrates the complete report processing workflow
    Manages validation, data collection, chart generation, and report rendering
    """
    
    def __init__(self, db: Session, 
                 data_aggregator=None, 
                 template_validator=None,
                 chart_generator=None,
                 pdf_generator=None,
                 excel_generator=None,
                 cache_service=None):
        self.db = db
        self.data_aggregator = data_aggregator
        self.template_validator = template_validator
        self.chart_generator = chart_generator
        self.pdf_generator = pdf_generator
        self.excel_generator = excel_generator
        self.cache_service = cache_service
        
        # Processing queue
        self.processing_queue: List[ProcessingJob] = []
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.completed_jobs: Dict[str, ProcessingJob] = {}
        
        # Processing steps configuration
        self.processing_steps = self._configure_processing_steps()
        
        # Monitoring
        self.max_concurrent_jobs = 3
        self.job_timeout_minutes = 30
        
    def submit_job(self, template_id: int, 
                   parameters: Dict[str, Any], 
                   priority: ProcessingPriority = ProcessingPriority.NORMAL,
                   job_id: Optional[str] = None) -> str:
        """
        Submit a new report processing job
        
        Args:
            template_id: Template to process
            parameters: Report parameters
            priority: Job priority
            job_id: Optional custom job ID
            
        Returns:
            Job ID for tracking
        """
        if not job_id:
            job_id = str(uuid.uuid4())
        
        job = ProcessingJob(
            job_id=job_id,
            template_id=template_id,
            parameters=parameters,
            priority=priority
        )
        
        # Insert into queue maintaining priority order
        inserted = False
        for i, queued_job in enumerate(self.processing_queue):
            if job.priority.value > queued_job.priority.value:
                self.processing_queue.insert(i, job)
                inserted = True
                break
        
        if not inserted:
            self.processing_queue.append(job)
        
        logger.info(f"Job {job_id} submitted for template {template_id} with priority {priority.name}")
        
        # Save job to database
        self._save_job_to_db(job)
        
        return job_id
    
    async def process_next_job(self) -> Optional[ProcessingJob]:
        """Process the next job in the queue"""
        
        if len(self.active_jobs) >= self.max_concurrent_jobs:
            logger.debug("Maximum concurrent jobs reached, waiting...")
            return None
        
        if not self.processing_queue:
            return None
        
        job = self.processing_queue.pop(0)
        self.active_jobs[job.job_id] = job
        
        logger.info(f"Starting processing for job {job.job_id}")
        
        try:
            await self._process_job(job)
        except Exception as e:
            logger.error(f"Job {job.job_id} failed with error: {str(e)}")
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
        finally:
            # Move job to completed
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
            self.completed_jobs[job.job_id] = job
            
            # Update database
            self._save_job_to_db(job)
        
        return job
    
    async def _process_job(self, job: ProcessingJob):
        """Process a single job through all steps"""
        
        job.started_at = datetime.now()
        job.status = ProcessingStatus.VALIDATING
        start_time = datetime.now()
        
        try:
            # Execute processing steps
            for step_name, step_config in self.processing_steps.items():
                if not await self._execute_step(job, step_name, step_config):
                    if step_config.required:
                        raise Exception(f"Required step '{step_name}' failed")
            
            # Mark as completed
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress_percentage = 100.0
            
            # Calculate total time
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            job.metrics.total_time_ms = int(total_time)
            
            logger.info(f"Job {job.job_id} completed successfully in {total_time:.0f}ms")
            
        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Job {job.job_id} failed: {str(e)}")
            raise e
    
    async def _execute_step(self, job: ProcessingJob, step_name: str, step_config: ProcessingStep) -> bool:
        """Execute a single processing step"""
        
        logger.debug(f"Job {job.job_id}: Executing step '{step_name}'")
        
        job.current_step = step_name
        step_start_time = datetime.now()
        
        try:
            # Check dependencies
            for dependency in step_config.dependencies:
                if dependency not in job.steps_completed:
                    raise Exception(f"Step '{step_name}' requires '{dependency}' to be completed first")
            
            # Execute step with timeout
            result = await asyncio.wait_for(
                step_config.function(job),
                timeout=step_config.timeout_seconds
            )
            
            # Record completion
            job.steps_completed.append(step_name)
            
            # Update step-specific metrics
            step_time = int((datetime.now() - step_start_time).total_seconds() * 1000)
            self._update_step_metrics(job, step_name, step_time)
            
            # Update progress
            progress_increment = 100.0 / len(self.processing_steps)
            job.progress_percentage = min(100.0, job.progress_percentage + progress_increment)
            
            logger.debug(f"Job {job.job_id}: Step '{step_name}' completed in {step_time}ms")
            
            return True
            
        except asyncio.TimeoutError:
            error_msg = f"Step '{step_name}' timed out after {step_config.timeout_seconds}s"
            logger.error(f"Job {job.job_id}: {error_msg}")
            job.steps_failed.append(step_name)
            job.metrics.errors_encountered += 1
            
            if step_config.required:
                raise Exception(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Step '{step_name}' failed: {str(e)}"
            logger.error(f"Job {job.job_id}: {error_msg}")
            job.steps_failed.append(step_name)
            job.metrics.errors_encountered += 1
            
            if step_config.required:
                raise e
            return False
    
    def _update_step_metrics(self, job: ProcessingJob, step_name: str, execution_time: int):
        """Update job metrics for completed step"""
        
        if step_name == 'validate_template':
            job.metrics.validation_time_ms = execution_time
        elif step_name == 'collect_data':
            job.metrics.data_collection_time_ms = execution_time
        elif step_name == 'generate_charts':
            job.metrics.chart_generation_time_ms = execution_time
        elif step_name == 'generate_report':
            job.metrics.report_generation_time_ms = execution_time
    
    def _configure_processing_steps(self) -> Dict[str, ProcessingStep]:
        """Configure the processing steps workflow"""
        
        return {
            'validate_template': ProcessingStep(
                name='Template Validation',
                function=self._step_validate_template,
                required=True,
                timeout_seconds=60,
                retry_count=1
            ),
            'collect_data': ProcessingStep(
                name='Data Collection',
                function=self._step_collect_data,
                required=True,
                timeout_seconds=300,
                retry_count=3,
                dependencies=['validate_template']
            ),
            'generate_charts': ProcessingStep(
                name='Chart Generation',
                function=self._step_generate_charts,
                required=False,
                timeout_seconds=180,
                retry_count=2,
                dependencies=['collect_data']
            ),
            'generate_report': ProcessingStep(
                name='Report Generation',
                function=self._step_generate_report,
                required=True,
                timeout_seconds=300,
                retry_count=2,
                dependencies=['collect_data']
            ),
            'finalize': ProcessingStep(
                name='Finalization',
                function=self._step_finalize,
                required=True,
                timeout_seconds=30,
                retry_count=1,
                dependencies=['generate_report']
            )
        }
    
    async def _step_validate_template(self, job: ProcessingJob) -> bool:
        """Validate template step"""
        
        job.status = ProcessingStatus.VALIDATING
        
        if not self.template_validator:
            logger.warning(f"Job {job.job_id}: No template validator configured, skipping validation")
            return True
        
        validation_result = self.template_validator.validate_template(
            job.template_id, run_tests=False
        )
        
        if not validation_result.is_valid:
            error_msg = f"Template validation failed: {validation_result.error_count} errors"
            raise Exception(error_msg)
        
        logger.info(f"Job {job.job_id}: Template validation passed")
        return True
    
    async def _step_collect_data(self, job: ProcessingJob) -> bool:
        """Data collection step"""
        
        job.status = ProcessingStatus.COLLECTING_DATA
        
        if not self.data_aggregator:
            raise Exception("Data aggregator not configured")
        
        # Get template configuration
        template = await self._get_template_config(job.template_id)
        data_sources = template.get('configuration', {}).get('data_sources', [])
        
        if not data_sources:
            logger.warning(f"Job {job.job_id}: No data sources configured")
            job.data = {}
            return True
        
        # Convert data sources to aggregator format
        from .data_aggregator import DataSource
        aggregator_sources = []
        
        for source in data_sources:
            aggregator_sources.append(DataSource(
                name=source['name'],
                endpoint=source['endpoint'],
                method=source.get('method', 'GET'),
                headers=source.get('headers', {}),
                params=source.get('params', {}),
                timeout=source.get('timeout', 30),
                cache_ttl=source.get('cache_ttl', 300),
                retry_count=source.get('retry_count', 3),
                required=source.get('required', True)
            ))
        
        # Collect data
        aggregation_result = await self.data_aggregator.aggregate_report_data(
            aggregator_sources, job.parameters, job.template_id
        )
        
        if not aggregation_result.success:
            error_msg = f"Data collection failed: {'; '.join(aggregation_result.errors)}"
            raise Exception(error_msg)
        
        # Store collected data
        job.data = aggregation_result.data
        job.metrics.data_sources_processed = len(aggregation_result.sources_collected)
        job.metrics.cache_hits = aggregation_result.cache_hits
        job.metrics.cache_misses = aggregation_result.cache_misses
        
        logger.info(f"Job {job.job_id}: Data collection completed - {len(aggregation_result.sources_collected)} sources")
        return True
    
    async def _step_generate_charts(self, job: ProcessingJob) -> bool:
        """Chart generation step"""
        
        job.status = ProcessingStatus.GENERATING_CHARTS
        
        if not self.chart_generator:
            logger.warning(f"Job {job.job_id}: No chart generator configured")
            return True
        
        # Get template chart configurations
        template = await self._get_template_config(job.template_id)
        charts = template.get('configuration', {}).get('charts', [])
        
        if not charts:
            logger.info(f"Job {job.job_id}: No charts configured")
            return True
        
        job.charts = {}
        
        for chart_config in charts:
            try:
                chart_data = self._extract_chart_data(job.data, chart_config)
                
                # Generate chart
                chart_result = await self.chart_generator.generate_chart(
                    chart_config['type'],
                    chart_data,
                    chart_config
                )
                
                job.charts[chart_config.get('id', f"chart_{len(job.charts)}")] = chart_result
                job.metrics.charts_generated += 1
                
            except Exception as e:
                logger.error(f"Job {job.job_id}: Chart generation failed: {str(e)}")
                if chart_config.get('required', False):
                    raise e
        
        logger.info(f"Job {job.job_id}: Generated {job.metrics.charts_generated} charts")
        return True
    
    async def _step_generate_report(self, job: ProcessingJob) -> bool:
        """Report generation step"""
        
        job.status = ProcessingStatus.RENDERING_REPORT
        
        template = await self._get_template_config(job.template_id)
        report_type = template.get('report_type', 'pdf')
        
        if report_type in ['pdf', 'both']:
            if not self.pdf_generator:
                raise Exception("PDF generator not configured")
            
            pdf_path = await self._generate_pdf_report(job, template)
            job.result_path = pdf_path
        
        if report_type in ['excel', 'both']:
            if not self.excel_generator:
                raise Exception("Excel generator not configured")
            
            excel_path = await self._generate_excel_report(job, template)
            if not job.result_path:
                job.result_path = excel_path
        
        logger.info(f"Job {job.job_id}: Report generation completed - {job.result_path}")
        return True
    
    async def _step_finalize(self, job: ProcessingJob) -> bool:
        """Finalization step"""
        
        # Clean up temporary data
        if hasattr(job, 'data'):
            # Keep only summary for metrics
            job.data = {'summary': 'Data processed successfully'}
        
        # Log completion
        logger.info(f"Job {job.job_id}: Processing finalized")
        return True
    
    async def _get_template_config(self, template_id: int) -> Dict[str, Any]:
        """Get template configuration from database"""
        
        query = """
            SELECT configuration, report_type, name
            FROM report_templates
            WHERE id = :template_id AND is_deleted = false
        """
        
        result = self.db.execute(text(query), {'template_id': template_id})
        row = result.fetchone()
        
        if not row:
            raise Exception(f"Template {template_id} not found")
        
        config = json.loads(row[0]) if row[0] else {}
        
        return {
            'configuration': config,
            'report_type': row[1],
            'name': row[2]
        }
    
    def _extract_chart_data(self, job_data: Dict[str, Any], chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for chart from job data"""
        
        data_source = chart_config.get('data_source')
        if not data_source or data_source not in job_data.get('raw_data', {}):
            raise Exception(f"Chart data source '{data_source}' not found in collected data")
        
        source_data = job_data['raw_data'][data_source]
        
        # Apply data transformations if specified
        x_field = chart_config.get('x_field', 'x')
        y_field = chart_config.get('y_field', 'y')
        
        if isinstance(source_data, dict) and 'data' in source_data:
            data_list = source_data['data']
        elif isinstance(source_data, list):
            data_list = source_data
        else:
            raise Exception(f"Unexpected data format for chart data source '{data_source}'")
        
        # Format data for chart
        chart_data = {
            'data': data_list,
            'x_field': x_field,
            'y_field': y_field,
            'title': chart_config.get('title', 'Chart'),
            'x_label': chart_config.get('x_label', x_field),
            'y_label': chart_config.get('y_label', y_field)
        }
        
        return chart_data
    
    async def _generate_pdf_report(self, job: ProcessingJob, template: Dict[str, Any]) -> str:
        """Generate PDF report"""
        
        if not self.pdf_generator:
            raise Exception("PDF generator not available")
        
        # Prepare report data
        report_data = {
            'title': f"{template['name']} Report",
            'generated_at': datetime.now().isoformat(),
            'parameters': job.parameters,
            'data': getattr(job, 'data', {}),
            'charts': getattr(job, 'charts', {}),
            'metrics': job.metrics.__dict__
        }
        
        # Generate PDF
        pdf_path = f"reports/job_{job.job_id}.pdf"
        await self.pdf_generator.generate_report(
            template_id=job.template_id,
            data=report_data,
            output_path=pdf_path,
            parameters=job.parameters
        )
        
        return pdf_path
    
    async def _generate_excel_report(self, job: ProcessingJob, template: Dict[str, Any]) -> str:
        """Generate Excel report"""
        
        if not self.excel_generator:
            raise Exception("Excel generator not available")
        
        # Prepare report data
        report_data = {
            'title': f"{template['name']} Report",
            'generated_at': datetime.now().isoformat(),
            'parameters': job.parameters,
            'data': getattr(job, 'data', {}),
            'charts': getattr(job, 'charts', {}),
            'metrics': job.metrics.__dict__
        }
        
        # Generate Excel
        excel_path = f"reports/job_{job.job_id}.xlsx"
        await self.excel_generator.generate_report(
            template_id=job.template_id,
            data=report_data,
            output_path=excel_path,
            parameters=job.parameters
        )
        
        return excel_path
    
    def _save_job_to_db(self, job: ProcessingJob):
        """Save job status to database"""
        
        try:
            # Save or update job in database
            upsert_query = """
                INSERT INTO report_processing_jobs 
                (job_id, template_id, status, priority, parameters, progress_percentage, 
                 current_step, result_path, error_message, metrics, created_at, started_at, completed_at)
                VALUES (:job_id, :template_id, :status, :priority, :parameters, :progress_percentage,
                        :current_step, :result_path, :error_message, :metrics, :created_at, :started_at, :completed_at)
                ON CONFLICT (job_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    progress_percentage = EXCLUDED.progress_percentage,
                    current_step = EXCLUDED.current_step,
                    result_path = EXCLUDED.result_path,
                    error_message = EXCLUDED.error_message,
                    metrics = EXCLUDED.metrics,
                    started_at = EXCLUDED.started_at,
                    completed_at = EXCLUDED.completed_at,
                    updated_at = NOW()
            """
            
            self.db.execute(text(upsert_query), {
                'job_id': job.job_id,
                'template_id': job.template_id,
                'status': job.status.value,
                'priority': job.priority.value,
                'parameters': json.dumps(job.parameters),
                'progress_percentage': job.progress_percentage,
                'current_step': job.current_step,
                'result_path': job.result_path,
                'error_message': job.error_message,
                'metrics': json.dumps(job.metrics.__dict__),
                'created_at': job.created_at,
                'started_at': job.started_at,
                'completed_at': job.completed_at
            })
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save job {job.job_id} to database: {str(e)}")
            self.db.rollback()
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status"""
        
        # Check active jobs
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
        elif job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
        else:
            # Check database
            query = """
                SELECT * FROM report_processing_jobs
                WHERE job_id = :job_id
            """
            result = self.db.execute(text(query), {'job_id': job_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            # Convert to dict
            columns = result.keys()
            job_data = dict(zip(columns, row))
            
            return {
                'job_id': job_data['job_id'],
                'template_id': job_data['template_id'],
                'status': job_data['status'],
                'progress_percentage': job_data['progress_percentage'],
                'current_step': job_data['current_step'],
                'result_path': job_data['result_path'],
                'error_message': job_data['error_message'],
                'created_at': job_data['created_at'].isoformat() if job_data['created_at'] else None,
                'started_at': job_data['started_at'].isoformat() if job_data['started_at'] else None,
                'completed_at': job_data['completed_at'].isoformat() if job_data['completed_at'] else None,
                'metrics': json.loads(job_data['metrics']) if job_data['metrics'] else {}
            }
        
        # Convert job object to dict
        return {
            'job_id': job.job_id,
            'template_id': job.template_id,
            'status': job.status.value,
            'progress_percentage': job.progress_percentage,
            'current_step': job.current_step,
            'result_path': job.result_path,
            'error_message': job.error_message,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'metrics': job.metrics.__dict__,
            'steps_completed': job.steps_completed,
            'steps_failed': job.steps_failed
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or active job"""
        
        # Remove from queue
        for i, job in enumerate(self.processing_queue):
            if job.job_id == job_id:
                job.status = ProcessingStatus.CANCELLED
                job.completed_at = datetime.now()
                del self.processing_queue[i]
                self.completed_jobs[job_id] = job
                self._save_job_to_db(job)
                logger.info(f"Job {job_id} cancelled (was queued)")
                return True
        
        # Mark active job for cancellation
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = ProcessingStatus.CANCELLED
            job.completed_at = datetime.now()
            logger.info(f"Job {job_id} marked for cancellation (was active)")
            return True
        
        return False
    
    async def run_processing_loop(self):
        """Main processing loop - runs continuously"""
        
        logger.info("Starting report processing loop")
        
        while True:
            try:
                # Process next job
                await self.process_next_job()
                
                # Cleanup old completed jobs
                self._cleanup_old_jobs()
                
                # Short delay before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Processing loop error: {str(e)}")
                await asyncio.sleep(5)  # Longer delay on error
    
    def _cleanup_old_jobs(self):
        """Clean up old completed jobs from memory"""
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        old_jobs = [
            job_id for job_id, job in self.completed_jobs.items()
            if job.completed_at and job.completed_at < cutoff_time
        ]
        
        for job_id in old_jobs:
            del self.completed_jobs[job_id]
        
        if old_jobs:
            logger.debug(f"Cleaned up {len(old_jobs)} old completed jobs")

# Factory function
def create_processing_orchestrator(db: Session, **services) -> ReportProcessingOrchestrator:
    """Create and configure processing orchestrator with services"""
    return ReportProcessingOrchestrator(db=db, **services)