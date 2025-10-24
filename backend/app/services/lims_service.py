"""
Laboratory Information Management System (LIMS) Service
Phase 5 Implementation - QMS Platform v3.0

Business logic for sample management, test execution, instrument tracking,
quality monitoring, and cross-module integration.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
import uuid
import hashlib
import json

from app.models.lims import (
    SampleType, Sample, TestMethod, TestSpecification,
    Instrument, TestExecution, TestResult, CalibrationRecord,
    SampleStatus, TestStatus, InstrumentStatus
)
from app.models.user import User
from app.schemas.lims import (
    SampleTypeCreate, SampleTypeUpdate,
    SampleCreate, SampleUpdate,
    TestMethodCreate, TestMethodUpdate,
    TestExecutionCreate, TestExecutionUpdate,
    TestResultCreate, TestResultUpdate,
    CalibrationRecordCreate, CalibrationRecordUpdate
)
from app.services.audit_service import AuditService
from app.services.quality_event_service import QualityEventService
from app.services.training_service import TrainingService


class LIMSService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.audit_service = AuditService(db, current_user)
        self.quality_event_service = QualityEventService(db, current_user)
        self.training_service = TrainingService(db, current_user)

    # Sample Type Management
    def create_sample_type(self, sample_type_data: SampleTypeCreate) -> SampleType:
        """Create a new sample type with validation"""
        # Check if code already exists
        existing = self.db.query(SampleType).filter(
            SampleType.code == sample_type_data.code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sample type with code '{sample_type_data.code}' already exists"
            )
        
        sample_type = SampleType(**sample_type_data.dict())
        self.db.add(sample_type)
        self.db.commit()
        self.db.refresh(sample_type)
        
        # Log creation
        self.audit_service.log_activity(
            entity_type="SampleType",
            entity_id=sample_type.id,
            action="CREATE",
            details=f"Created sample type: {sample_type.name}"
        )
        
        return sample_type

    def get_sample_type(self, sample_type_id: int) -> SampleType:
        """Get sample type by ID"""
        sample_type = self.db.query(SampleType).filter(
            SampleType.id == sample_type_id
        ).first()
        if not sample_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample type not found"
            )
        return sample_type

    def list_sample_types(
        self, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[SampleType]:
        """List sample types with filtering"""
        query = self.db.query(SampleType)
        
        if category:
            query = query.filter(SampleType.category == category)
        
        return query.offset(skip).limit(limit).all()

    def update_sample_type(
        self, 
        sample_type_id: int, 
        sample_type_data: SampleTypeUpdate
    ) -> SampleType:
        """Update sample type"""
        sample_type = self.get_sample_type(sample_type_id)
        
        update_data = sample_type_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sample_type, field, value)
        
        self.db.commit()
        self.db.refresh(sample_type)
        
        # Log update
        self.audit_service.log_activity(
            entity_type="SampleType",
            entity_id=sample_type.id,
            action="UPDATE",
            details=f"Updated sample type: {sample_type.name}"
        )
        
        return sample_type

    # Sample Management
    def register_sample(self, sample_data: SampleCreate) -> Sample:
        """Register a new sample with automatic ID generation"""
        # Validate sample type exists
        sample_type = self.get_sample_type(sample_data.sample_type_id)
        
        # Generate unique sample ID if not provided
        if not sample_data.sample_id:
            sample_data.sample_id = self._generate_sample_id(sample_type)
        
        # Check if sample ID already exists
        existing = self.db.query(Sample).filter(
            Sample.sample_id == sample_data.sample_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sample with ID '{sample_data.sample_id}' already exists"
            )
        
        # Create sample with chain of custody
        sample_dict = sample_data.dict()
        sample_dict['received_by_id'] = sample_data.received_by_id or self.current_user.id
        sample_dict['current_custodian_id'] = self.current_user.id
        sample_dict['chain_of_custody'] = self._initialize_chain_of_custody(sample_dict)
        
        sample = Sample(**sample_dict)
        self.db.add(sample)
        self.db.commit()
        self.db.refresh(sample)
        
        # Log sample registration
        self.audit_service.log_activity(
            entity_type="Sample",
            entity_id=sample.id,
            action="REGISTER",
            details=f"Registered sample: {sample.sample_id}"
        )
        
        return sample

    def get_sample(self, sample_id: int, include_chain_of_custody: bool = False) -> Sample:
        """Get sample by ID with optional chain of custody"""
        sample = self.db.query(Sample).filter(Sample.id == sample_id).first()
        if not sample:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sample not found"
            )
        return sample

    def list_samples(
        self,
        skip: int = 0,
        limit: int = 100,
        sample_type_id: Optional[int] = None,
        status: Optional[str] = None,
        batch_lot_number: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Sample]:
        """List samples with comprehensive filtering"""
        query = self.db.query(Sample)
        
        if sample_type_id:
            query = query.filter(Sample.sample_type_id == sample_type_id)
        
        if status:
            query = query.filter(Sample.status == status)
        
        if batch_lot_number:
            query = query.filter(Sample.batch_lot_number.ilike(f"%{batch_lot_number}%"))
        
        if date_from:
            query = query.filter(Sample.received_date >= date_from)
        
        if date_to:
            query = query.filter(Sample.received_date <= date_to)
        
        return query.offset(skip).limit(limit).all()

    def update_sample(self, sample_id: int, sample_data: SampleUpdate) -> Sample:
        """Update sample information"""
        sample = self.get_sample(sample_id)
        
        update_data = sample_data.dict(exclude_unset=True)
        
        # Handle custody transfer
        if 'current_custodian_id' in update_data:
            self._update_chain_of_custody(
                sample, 
                update_data['current_custodian_id'],
                "Custody transfer via API"
            )
        
        # Handle status changes
        if 'status' in update_data:
            old_status = sample.status
            new_status = update_data['status']
            if not self._is_valid_sample_status_transition(old_status, new_status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition from {old_status} to {new_status}"
                )
        
        for field, value in update_data.items():
            setattr(sample, field, value)
        
        self.db.commit()
        self.db.refresh(sample)
        
        # Log update
        self.audit_service.log_activity(
            entity_type="Sample",
            entity_id=sample.id,
            action="UPDATE",
            details=f"Updated sample: {sample.sample_id}"
        )
        
        return sample

    def transfer_sample_custody(
        self, 
        sample_id: int, 
        new_custodian_id: int, 
        transfer_reason: str
    ) -> Sample:
        """Transfer sample custody with audit trail"""
        sample = self.get_sample(sample_id)
        
        # Validate new custodian exists
        new_custodian = self.db.query(User).filter(User.id == new_custodian_id).first()
        if not new_custodian:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New custodian not found"
            )
        
        old_custodian_id = sample.current_custodian_id
        sample.current_custodian_id = new_custodian_id
        
        # Update chain of custody
        self._update_chain_of_custody(sample, new_custodian_id, transfer_reason)
        
        self.db.commit()
        self.db.refresh(sample)
        
        # Log custody transfer
        self.audit_service.log_activity(
            entity_type="Sample",
            entity_id=sample.id,
            action="CUSTODY_TRANSFER",
            details=f"Transferred custody from user {old_custodian_id} to {new_custodian_id}: {transfer_reason}"
        )
        
        return sample

    # Test Execution Management
    def start_test_execution(self, execution_data: TestExecutionCreate) -> TestExecution:
        """Start a new test execution with validation"""
        # Validate sample exists and is available for testing
        sample = self.get_sample(execution_data.sample_id)
        if sample.status not in [SampleStatus.RECEIVED, SampleStatus.IN_TESTING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sample status {sample.status} is not valid for testing"
            )
        
        # Validate test method exists and is approved
        test_method = self.db.query(TestMethod).filter(
            TestMethod.id == execution_data.test_method_id
        ).first()
        if not test_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test method not found"
            )
        
        if test_method.validation_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test method is not approved for use"
            )
        
        # Verify analyst qualifications
        self._verify_analyst_qualifications(self.current_user.id, test_method.id)
        
        # Validate instrument availability if specified
        if execution_data.instrument_id:
            instrument = self.db.query(Instrument).filter(
                Instrument.id == execution_data.instrument_id
            ).first()
            if not instrument or instrument.status != InstrumentStatus.QUALIFIED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Instrument is not available or qualified"
                )
        
        # Generate execution ID
        execution_dict = execution_data.dict()
        execution_dict['execution_id'] = self._generate_execution_id()
        execution_dict['analyst_id'] = self.current_user.id
        
        execution = TestExecution(**execution_dict)
        self.db.add(execution)
        
        # Update sample status to in_testing
        sample.status = SampleStatus.IN_TESTING
        
        self.db.commit()
        self.db.refresh(execution)
        
        # Log execution start
        self.audit_service.log_activity(
            entity_type="TestExecution",
            entity_id=execution.id,
            action="START",
            details=f"Started test execution: {execution.execution_id}"
        )
        
        return execution

    def record_test_result(self, result_data: TestResultCreate) -> TestResult:
        """Record a test result with automatic compliance checking"""
        # Validate test execution exists
        execution = self.db.query(TestExecution).filter(
            TestExecution.id == result_data.test_execution_id
        ).first()
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test execution not found"
            )
        
        # Validate test specification exists
        specification = self.db.query(TestSpecification).filter(
            TestSpecification.id == result_data.test_specification_id
        ).first()
        if not specification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test specification not found"
            )
        
        # Create test result
        result_dict = result_data.dict()
        
        # Calculate compliance and statistics
        compliance_data = self._calculate_result_compliance(result_dict, specification)
        result_dict.update(compliance_data)
        
        # Generate data integrity hash
        result_dict['data_hash'] = self._generate_data_hash(result_dict)
        
        result = TestResult(**result_dict)
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        # Check for OOS and trigger quality events
        if result.out_of_specification:
            self._trigger_oos_quality_event(result, execution, specification)
        
        # Log result recording
        self.audit_service.log_activity(
            entity_type="TestResult",
            entity_id=result.id,
            action="RECORD",
            details=f"Recorded test result: {result.parameter_name} = {result.result_value}"
        )
        
        return result

    # Dashboard and Analytics
    def get_lims_dashboard(self) -> Dict[str, Any]:
        """Generate real-time LIMS dashboard data"""
        today = datetime.utcnow().date()
        
        return {
            "total_samples": self.db.query(Sample).count(),
            "samples_in_testing": self.db.query(Sample).filter(
                Sample.status == SampleStatus.IN_TESTING
            ).count(),
            "samples_completed_today": self.db.query(Sample).filter(
                and_(
                    Sample.status == SampleStatus.TESTING_COMPLETE,
                    func.date(Sample.updated_at) == today
                )
            ).count(),
            "overdue_tests": self._get_overdue_tests_count(),
            "oos_results_today": self._get_oos_results_count(today),
            "instruments_due_calibration": self._get_instruments_due_calibration_count(),
            "analyst_workload": self._get_analyst_workload(),
            "recent_completions": self._get_recent_completions(),
            "upcoming_calibrations": self._get_upcoming_calibrations()
        }

    # Helper Methods
    def _generate_sample_id(self, sample_type: SampleType) -> str:
        """Generate unique sample ID"""
        year = datetime.utcnow().year
        sequence = self.db.query(Sample).filter(
            Sample.sample_id.like(f"{sample_type.code}-{year}-%")
        ).count() + 1
        return f"{sample_type.code}-{year}-{sequence:05d}"

    def _generate_execution_id(self) -> str:
        """Generate unique test execution ID"""
        return f"EXE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    def _initialize_chain_of_custody(self, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize chain of custody record"""
        return {
            "events": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": "RECEIVED",
                    "user_id": sample_data.get('received_by_id'),
                    "location": sample_data.get('storage_location'),
                    "notes": f"Sample received from {sample_data.get('collected_by', 'unknown')}"
                }
            ]
        }

    def _update_chain_of_custody(
        self, 
        sample: Sample, 
        new_custodian_id: int, 
        reason: str
    ) -> None:
        """Update chain of custody with new event"""
        if not sample.chain_of_custody:
            sample.chain_of_custody = {"events": []}
        
        sample.chain_of_custody["events"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "CUSTODY_TRANSFER",
            "from_user_id": sample.current_custodian_id,
            "to_user_id": new_custodian_id,
            "reason": reason,
            "transferred_by": self.current_user.id
        })

    def _verify_analyst_qualifications(self, analyst_id: int, test_method_id: int) -> bool:
        """Verify analyst has required qualifications for test method"""
        test_method = self.db.query(TestMethod).filter(
            TestMethod.id == test_method_id
        ).first()
        
        if not test_method.analyst_qualifications:
            return True  # No specific qualifications required
        
        # Check with training service for analyst qualifications
        # This would integrate with the TRM module
        try:
            is_qualified = self.training_service.verify_analyst_competency(
                analyst_id, 
                test_method_id
            )
            if not is_qualified:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Analyst does not have required qualifications for this test method"
                )
            return True
        except Exception:
            # If training service is not available, allow execution but log warning
            self.audit_service.log_activity(
                entity_type="TestExecution",
                entity_id=None,
                action="QUALIFICATION_WARNING",
                details=f"Could not verify analyst qualifications for method {test_method_id}"
            )
            return True

    def _calculate_result_compliance(
        self, 
        result_data: Dict[str, Any], 
        specification: TestSpecification
    ) -> Dict[str, Any]:
        """Calculate compliance and statistical data for test result"""
        result_value = result_data.get('result_value')
        replicate_values = result_data.get('replicate_values', [])
        
        compliance_data = {
            "pass_fail": True,
            "out_of_specification": False,
            "deviation_percent": None
        }
        
        if result_value is not None:
            # Check specification limits
            if specification.lower_limit is not None and result_value < specification.lower_limit:
                compliance_data["pass_fail"] = False
                compliance_data["out_of_specification"] = True
            
            if specification.upper_limit is not None and result_value > specification.upper_limit:
                compliance_data["pass_fail"] = False
                compliance_data["out_of_specification"] = True
            
            # Calculate deviation from target
            if specification.target_value is not None:
                compliance_data["deviation_percent"] = (
                    (result_value - specification.target_value) / specification.target_value * 100
                )
        
        # Calculate statistics for replicates
        if replicate_values and len(replicate_values) > 1:
            import statistics
            compliance_data.update({
                "mean_value": statistics.mean(replicate_values),
                "standard_deviation": statistics.stdev(replicate_values),
                "relative_standard_deviation": (
                    statistics.stdev(replicate_values) / statistics.mean(replicate_values) * 100
                )
            })
        
        return compliance_data

    def _generate_data_hash(self, result_data: Dict[str, Any]) -> str:
        """Generate hash for data integrity verification"""
        # Create a consistent string representation for hashing
        hash_data = {
            "parameter_name": result_data.get("parameter_name"),
            "result_value": result_data.get("result_value"),
            "result_text": result_data.get("result_text"),
            "timestamp": datetime.utcnow().isoformat()
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _trigger_oos_quality_event(
        self, 
        result: TestResult, 
        execution: TestExecution, 
        specification: TestSpecification
    ) -> None:
        """Trigger automatic quality event for OOS results"""
        try:
            quality_event_data = {
                "event_type": "OOS_RESULT",
                "severity": "high" if specification.regulatory_requirement else "medium",
                "description": f"Out of specification result for {result.parameter_name}",
                "source_reference": f"Test Execution {execution.execution_id}",
                "details": {
                    "sample_id": execution.sample.sample_id,
                    "test_method": execution.test_method.method_code,
                    "parameter": result.parameter_name,
                    "result_value": result.result_value,
                    "specification_limits": {
                        "lower": specification.lower_limit,
                        "upper": specification.upper_limit
                    }
                },
                "automatic_trigger": True
            }
            
            # Create quality event through QRM service
            self.quality_event_service.create_quality_event(quality_event_data)
            
        except Exception as e:
            # Log error but don't fail the result recording
            self.audit_service.log_activity(
                entity_type="TestResult",
                entity_id=result.id,
                action="QE_TRIGGER_ERROR",
                details=f"Failed to trigger quality event for OOS result: {str(e)}"
            )

    def _is_valid_sample_status_transition(
        self, 
        current_status: SampleStatus, 
        new_status: SampleStatus
    ) -> bool:
        """Validate sample status transitions"""
        valid_transitions = {
            SampleStatus.RECEIVED: [SampleStatus.IN_TESTING, SampleStatus.DISPOSED],
            SampleStatus.IN_TESTING: [SampleStatus.TESTING_COMPLETE, SampleStatus.RECEIVED],
            SampleStatus.TESTING_COMPLETE: [SampleStatus.APPROVED, SampleStatus.REJECTED],
            SampleStatus.APPROVED: [SampleStatus.DISPOSED],
            SampleStatus.REJECTED: [SampleStatus.DISPOSED, SampleStatus.IN_TESTING]
        }
        
        return new_status in valid_transitions.get(current_status, [])

    def _get_overdue_tests_count(self) -> int:
        """Get count of overdue test executions"""
        return self.db.query(TestExecution).filter(
            and_(
                TestExecution.status.in_([TestStatus.PENDING, TestStatus.IN_PROGRESS]),
                TestExecution.start_datetime < datetime.utcnow() - timedelta(days=1)
            )
        ).count()

    def _get_oos_results_count(self, date: date) -> int:
        """Get count of OOS results for a specific date"""
        return self.db.query(TestResult).filter(
            and_(
                TestResult.out_of_specification == True,
                func.date(TestResult.created_at) == date
            )
        ).count()

    def _get_instruments_due_calibration_count(self) -> int:
        """Get count of instruments due for calibration"""
        return self.db.query(Instrument).filter(
            or_(
                Instrument.next_calibration_due <= datetime.utcnow().date(),
                Instrument.status == InstrumentStatus.CALIBRATION_DUE
            )
        ).count()

    def _get_analyst_workload(self) -> Dict[str, int]:
        """Get current workload by analyst"""
        workload = self.db.query(
            User.username,
            func.count(TestExecution.id).label('active_tests')
        ).join(
            TestExecution, User.id == TestExecution.analyst_id
        ).filter(
            TestExecution.status.in_([TestStatus.PENDING, TestStatus.IN_PROGRESS])
        ).group_by(User.id, User.username).all()
        
        return {username: count for username, count in workload}

    def _get_recent_completions(self) -> List[Dict[str, Any]]:
        """Get recently completed test executions"""
        recent = self.db.query(TestExecution).filter(
            TestExecution.status == TestStatus.COMPLETED
        ).order_by(desc(TestExecution.completion_datetime)).limit(10).all()
        
        return [
            {
                "execution_id": exe.execution_id,
                "sample_id": exe.sample.sample_id,
                "test_method": exe.test_method.title,
                "completion_time": exe.completion_datetime,
                "analyst": exe.analyst.username
            }
            for exe in recent
        ]

    def _get_upcoming_calibrations(self) -> List[Dict[str, Any]]:
        """Get upcoming instrument calibrations"""
        upcoming = self.db.query(Instrument).filter(
            Instrument.next_calibration_due <= datetime.utcnow().date() + timedelta(days=30)
        ).order_by(Instrument.next_calibration_due).limit(10).all()
        
        return [
            {
                "instrument_id": inst.instrument_id,
                "name": inst.name,
                "due_date": inst.next_calibration_due,
                "days_until_due": (inst.next_calibration_due - datetime.utcnow().date()).days
            }
            for inst in upcoming
        ]

    # Instrument and Calibration Management
    def register_instrument(self, instrument_data: InstrumentCreate) -> Instrument:
        """Register a new laboratory instrument"""
        # Check if instrument ID already exists
        existing = self.db.query(Instrument).filter(
            Instrument.instrument_id == instrument_data.instrument_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instrument with ID '{instrument_data.instrument_id}' already exists"
            )
        
        instrument_dict = instrument_data.dict()
        # Calculate initial calibration due date
        if instrument_dict.get('calibration_frequency_days'):
            instrument_dict['next_calibration_due'] = (
                datetime.utcnow().date() + 
                timedelta(days=instrument_dict['calibration_frequency_days'])
            )
        
        instrument = Instrument(**instrument_dict)
        self.db.add(instrument)
        self.db.commit()
        self.db.refresh(instrument)
        
        # Log instrument registration
        self.audit_service.log_activity(
            entity_type="Instrument",
            entity_id=instrument.id,
            action="REGISTER",
            details=f"Registered instrument: {instrument.name}"
        )
        
        return instrument

    def record_calibration(self, calibration_data: CalibrationRecordCreate) -> CalibrationRecord:
        """Record instrument calibration with automatic status updates"""
        # Validate instrument exists
        instrument = self.db.query(Instrument).filter(
            Instrument.id == calibration_data.instrument_id
        ).first()
        if not instrument:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found"
            )
        
        # Create calibration record
        calibration_dict = calibration_data.dict()
        calibration_dict['performed_by_id'] = self.current_user.id
        
        calibration = CalibrationRecord(**calibration_dict)
        self.db.add(calibration)
        
        # Update instrument calibration status
        instrument.last_calibration_date = calibration.calibration_date
        instrument.next_calibration_due = calibration.next_due_date
        
        # Update instrument status based on calibration result
        if calibration.overall_result == "PASS":
            instrument.status = InstrumentStatus.QUALIFIED
        else:
            instrument.status = InstrumentStatus.OUT_OF_SERVICE
        
        self.db.commit()
        self.db.refresh(calibration)
        
        # Log calibration
        self.audit_service.log_activity(
            entity_type="CalibrationRecord",
            entity_id=calibration.id,
            action="RECORD",
            details=f"Recorded calibration for {instrument.name}: {calibration.overall_result}"
        )
        
        return calibration

    # Advanced Analytics and Reporting
    def get_laboratory_efficiency_report(
        self, 
        start_date: date, 
        end_date: date,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive laboratory efficiency report"""
        # Base query for the period
        base_query = self.db.query(TestExecution).filter(
            and_(
                TestExecution.completion_datetime >= start_date,
                TestExecution.completion_datetime <= end_date,
                TestExecution.status == TestStatus.COMPLETED
            )
        )
        
        if department:
            base_query = base_query.join(Instrument).filter(
                Instrument.department == department
            )
        
        completed_tests = base_query.all()
        
        # Calculate efficiency metrics
        total_samples = len(set(test.sample_id for test in completed_tests))
        
        # Calculate average turnaround time
        turnaround_times = []
        for test in completed_tests:
            if test.start_datetime and test.completion_datetime:
                delta = test.completion_datetime - test.start_datetime
                turnaround_times.append(delta.total_seconds() / 3600)  # Convert to hours
        
        avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
        
        # Calculate OOS rate
        total_results = self.db.query(TestResult).join(TestExecution).filter(
            and_(
                TestExecution.completion_datetime >= start_date,
                TestExecution.completion_datetime <= end_date
            )
        ).count()
        
        oos_results = self.db.query(TestResult).join(TestExecution).filter(
            and_(
                TestExecution.completion_datetime >= start_date,
                TestExecution.completion_datetime <= end_date,
                TestResult.out_of_specification == True
            )
        ).count()
        
        oos_rate = (oos_results / total_results * 100) if total_results > 0 else 0
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_samples_processed": total_samples,
            "total_tests_completed": len(completed_tests),
            "average_turnaround_time_hours": round(avg_turnaround, 2),
            "on_time_completion_rate": self._calculate_on_time_rate(completed_tests),
            "oos_rate": round(oos_rate, 2),
            "instrument_utilization": self._calculate_instrument_utilization(start_date, end_date),
            "analyst_productivity": self._calculate_analyst_productivity(start_date, end_date)
        }

    def get_quality_trend_analysis(
        self,
        parameter_name: Optional[str] = None,
        sample_type_id: Optional[int] = None,
        test_method_id: Optional[int] = None,
        period_days: int = 90
    ) -> List[Dict[str, Any]]:
        """Generate quality trend analysis for specified parameters"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=period_days)
        
        # Build base query
        query = self.db.query(TestResult).join(TestExecution).join(TestSpecification)
        
        # Apply filters
        query = query.filter(
            func.date(TestResult.created_at) >= start_date
        )
        
        if parameter_name:
            query = query.filter(TestResult.parameter_name == parameter_name)
        
        if sample_type_id:
            query = query.join(Sample).filter(Sample.sample_type_id == sample_type_id)
        
        if test_method_id:
            query = query.filter(TestSpecification.test_method_id == test_method_id)
        
        results = query.all()
        
        # Group results by parameter and analyze trends
        trends = {}
        for result in results:
            key = f"{result.parameter_name}_{result.test_specification.sample_type_id}_{result.test_specification.test_method_id}"
            
            if key not in trends:
                trends[key] = {
                    "parameter_name": result.parameter_name,
                    "sample_type_id": result.test_specification.sample_type_id,
                    "test_method_id": result.test_specification.test_method_id,
                    "values": [],
                    "dates": []
                }
            
            if result.result_value is not None:
                trends[key]["values"].append(result.result_value)
                trends[key]["dates"].append(result.created_at.date())
        
        # Analyze each trend
        trend_analyses = []
        for trend_data in trends.values():
            if len(trend_data["values"]) >= 5:  # Minimum data points for analysis
                analysis = self._analyze_parameter_trend(trend_data, start_date, end_date)
                trend_analyses.append(analysis)
        
        return trend_analyses

    def get_sample_workflow_status(self, sample_id: int) -> Dict[str, Any]:
        """Get complete workflow status for a sample"""
        sample = self.get_sample(sample_id)
        
        # Get all test executions for this sample
        executions = self.db.query(TestExecution).filter(
            TestExecution.sample_id == sample_id
        ).all()
        
        # Count test statuses
        total_tests = len(executions)
        completed_tests = len([e for e in executions if e.status == TestStatus.COMPLETED])
        approved_tests = len([e for e in executions if e.status == TestStatus.APPROVED])
        
        # Check for OOS results
        oos_count = self.db.query(TestResult).join(TestExecution).filter(
            and_(
                TestExecution.sample_id == sample_id,
                TestResult.out_of_specification == True
            )
        ).count()
        
        # Calculate completion percentage
        completion_percentage = (completed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Estimate completion time based on remaining tests
        estimated_completion = None
        if total_tests > completed_tests:
            avg_test_duration = self._get_average_test_duration()
            remaining_tests = total_tests - completed_tests
            estimated_completion = datetime.utcnow() + timedelta(hours=avg_test_duration * remaining_tests)
        
        return {
            "sample_id": sample.sample_id,
            "sample_status": sample.status,
            "tests_assigned": total_tests,
            "tests_completed": completed_tests,
            "tests_approved": approved_tests,
            "oos_results": oos_count,
            "completion_percentage": round(completion_percentage, 1),
            "estimated_completion": estimated_completion
        }

    # Bulk Operations
    def bulk_assign_tests(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk assign tests to multiple samples"""
        sample_ids = assignment_data["sample_ids"]
        test_method_ids = assignment_data["test_method_ids"]
        
        successful = 0
        failed = 0
        errors = []
        
        for sample_id in sample_ids:
            for test_method_id in test_method_ids:
                try:
                    execution_data = TestExecutionCreate(
                        sample_id=sample_id,
                        test_method_id=test_method_id,
                        execution_id=self._generate_execution_id(),
                        start_datetime=datetime.utcnow()
                    )
                    self.start_test_execution(execution_data)
                    successful += 1
                except Exception as e:
                    failed += 1
                    errors.append({
                        "sample_id": str(sample_id),
                        "test_method_id": str(test_method_id),
                        "error": str(e)
                    })
        
        return {
            "successful_operations": successful,
            "failed_operations": failed,
            "total_requested": len(sample_ids) * len(test_method_ids),
            "errors": errors,
            "success_rate": round(successful / (successful + failed) * 100, 1) if (successful + failed) > 0 else 0
        }

    # Helper Methods for Analytics
    def _calculate_on_time_rate(self, completed_tests: List[TestExecution]) -> float:
        """Calculate percentage of tests completed on time"""
        on_time = 0
        total = 0
        
        for test in completed_tests:
            if test.test_method.estimated_duration_hours:
                expected_completion = test.start_datetime + timedelta(
                    hours=test.test_method.estimated_duration_hours
                )
                if test.completion_datetime <= expected_completion:
                    on_time += 1
                total += 1
        
        return round(on_time / total * 100, 1) if total > 0 else 0

    def _calculate_instrument_utilization(self, start_date: date, end_date: date) -> Dict[str, float]:
        """Calculate instrument utilization rates"""
        instruments = self.db.query(Instrument).all()
        utilization = {}
        
        for instrument in instruments:
            # Count test executions using this instrument
            test_count = self.db.query(TestExecution).filter(
                and_(
                    TestExecution.instrument_id == instrument.id,
                    func.date(TestExecution.start_datetime) >= start_date,
                    func.date(TestExecution.start_datetime) <= end_date
                )
            ).count()
            
            # Calculate utilization based on available days
            period_days = (end_date - start_date).days + 1
            # Assume 8 hours per day, 1 test per hour max capacity
            max_capacity = period_days * 8
            utilization[instrument.name] = round(test_count / max_capacity * 100, 1) if max_capacity > 0 else 0
        
        return utilization

    def _calculate_analyst_productivity(self, start_date: date, end_date: date) -> Dict[str, Dict[str, Any]]:
        """Calculate analyst productivity metrics"""
        analysts = self.db.query(User).filter(User.is_active == True).all()
        productivity = {}
        
        for analyst in analysts:
            # Get completed tests by this analyst
            completed_tests = self.db.query(TestExecution).filter(
                and_(
                    TestExecution.analyst_id == analyst.id,
                    TestExecution.status == TestStatus.COMPLETED,
                    func.date(TestExecution.completion_datetime) >= start_date,
                    func.date(TestExecution.completion_datetime) <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_tests = len(completed_tests)
            avg_time = 0
            if completed_tests:
                total_time = sum([
                    (test.completion_datetime - test.start_datetime).total_seconds() / 3600
                    for test in completed_tests 
                    if test.completion_datetime and test.start_datetime
                ])
                avg_time = total_time / total_tests if total_tests > 0 else 0
            
            productivity[analyst.username] = {
                "tests_completed": total_tests,
                "average_time_hours": round(avg_time, 2),
                "productivity_score": round(total_tests / avg_time if avg_time > 0 else 0, 2)
            }
        
        return productivity

    def _analyze_parameter_trend(self, trend_data: Dict[str, Any], start_date: date, end_date: date) -> Dict[str, Any]:
        """Analyze trend for a specific parameter"""
        values = trend_data["values"]
        
        if len(values) < 5:
            return None
        
        # Calculate basic statistics
        import statistics
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Simple trend analysis (linear regression would be more accurate)
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg * 1.05:
            trend_direction = "improving"
        elif second_avg < first_avg * 0.95:
            trend_direction = "deteriorating"
        else:
            trend_direction = "stable"
        
        # Calculate control limits (3-sigma)
        upper_control = mean_value + (3 * std_dev)
        lower_control = mean_value - (3 * std_dev)
        
        # Count out-of-trend points
        out_of_trend = len([v for v in values if v > upper_control or v < lower_control])
        
        return {
            "parameter_name": trend_data["parameter_name"],
            "sample_type_id": trend_data["sample_type_id"],
            "test_method_id": trend_data["test_method_id"],
            "period_start": start_date,
            "period_end": end_date,
            "total_results": len(values),
            "mean_value": round(mean_value, 4),
            "standard_deviation": round(std_dev, 4),
            "trend_direction": trend_direction,
            "control_limits": {
                "upper": round(upper_control, 4),
                "lower": round(lower_control, 4)
            },
            "out_of_trend_points": out_of_trend,
            "recommended_actions": self._get_trend_recommendations(trend_direction, out_of_trend, len(values))
        }

    def _get_trend_recommendations(self, trend_direction: str, out_of_trend: int, total_points: int) -> List[str]:
        """Get recommendations based on trend analysis"""
        recommendations = []
        
        if trend_direction == "deteriorating":
            recommendations.append("Investigate potential process degradation")
            recommendations.append("Review method parameters and environmental conditions")
            recommendations.append("Consider recalibration of instruments")
        
        if out_of_trend / total_points > 0.1:  # More than 10% out of trend
            recommendations.append("Investigate out-of-control points")
            recommendations.append("Review analyst training and method compliance")
            recommendations.append("Consider process capability study")
        
        if not recommendations:
            recommendations.append("Process appears stable - continue monitoring")
        
        return recommendations

    def _get_average_test_duration(self) -> float:
        """Get average test duration across all methods"""
        avg_duration = self.db.query(func.avg(TestMethod.estimated_duration_hours)).scalar()
        return avg_duration or 2.0  # Default 2 hours if no data