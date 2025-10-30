"""
Laboratory Information Management System (LIMS) Models
Phase 5 Implementation - QMS Platform v3.0

Core models for sample management, test execution, instrument tracking,
and laboratory data integrity.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Numeric, ForeignKey, Enum, JSON, Date, Time
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel


class SampleCategory(str, enum.Enum):
    """Categories of laboratory samples"""
    RAW_MATERIAL = "raw_material"
    FINISHED_PRODUCT = "finished_product"
    IN_PROCESS = "in_process"
    STABILITY = "stability"
    REFERENCE_STANDARD = "reference_standard"
    ENVIRONMENTAL = "environmental"


class SampleStatus(str, enum.Enum):
    """Sample lifecycle status"""
    RECEIVED = "received"
    IN_TESTING = "in_testing"
    TESTING_COMPLETE = "testing_complete"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPOSED = "disposed"


class TestStatus(str, enum.Enum):
    """Test execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class InstrumentStatus(str, enum.Enum):
    """Instrument qualification status"""
    QUALIFIED = "qualified"
    CALIBRATION_DUE = "calibration_due"
    OUT_OF_SERVICE = "out_of_service"
    MAINTENANCE_REQUIRED = "maintenance_required"


class SampleType(BaseModel):
    """Define different types of laboratory samples"""
    __tablename__ = "sample_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(Enum(SampleCategory), nullable=False)
    description = Column(Text)
    
    # Storage and handling requirements
    storage_temperature_min = Column(Numeric(5, 2))
    storage_temperature_max = Column(Numeric(5, 2))
    storage_humidity_max = Column(Numeric(5, 2))
    storage_conditions = Column(Text)
    shelf_life_days = Column(Integer)
    
    # Safety and regulatory
    hazard_classification = Column(String(100))
    regulatory_category = Column(String(100))
    disposal_instructions = Column(Text)
    
    # Relationships
    samples = relationship("Sample", back_populates="sample_type")
    test_specifications = relationship("TestSpecification", back_populates="sample_type")
    
    def __repr__(self):
        return f"<SampleType {self.code}: {self.name}>"


class Sample(BaseModel):
    """Individual sample tracking and chain of custody"""
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String(50), unique=True, nullable=False, index=True)
    sample_type_id = Column(Integer, ForeignKey("sample_types.id"), nullable=False)
    
    # Sample identification
    batch_lot_number = Column(String(100), nullable=False, index=True)
    supplier_reference = Column(String(100))
    internal_reference = Column(String(100))
    
    # Sample details
    collection_date = Column(DateTime, nullable=False)
    received_date = Column(DateTime, default=func.now())
    expiry_date = Column(DateTime)
    quantity = Column(Numeric(10, 3))
    quantity_units = Column(String(20))
    
    # Location and custody
    storage_location = Column(String(200))
    collected_by = Column(String(200))
    received_by_id = Column(Integer, ForeignKey("users.id"))
    current_custodian_id = Column(Integer, ForeignKey("users.id"))
    
    # Status and conditions
    status = Column(Enum(SampleStatus), default=SampleStatus.RECEIVED)
    temperature_on_receipt = Column(Numeric(5, 2))
    condition_on_receipt = Column(Text)
    chain_of_custody = Column(JSON)  # Complete custody trail
    
    # Special handling
    priority_level = Column(String(20), default="normal")
    special_instructions = Column(Text)
    
    # Relationships
    sample_type = relationship("SampleType", back_populates="samples")
    received_by = relationship("User", foreign_keys=[received_by_id])
    current_custodian = relationship("User", foreign_keys=[current_custodian_id])
    test_executions = relationship("TestExecution", back_populates="sample")
    
    def __repr__(self):
        return f"<Sample {self.sample_id}: {self.batch_lot_number}>"


class TestMethod(BaseModel):
    """Analytical test procedures and methods"""
    __tablename__ = "test_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    method_code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text)
    
    # Method details
    procedure_document_id = Column(Integer, ForeignKey("documents.id"))
    method_type = Column(String(100))  # HPLC, GC, UV, etc.
    estimated_duration_hours = Column(Numeric(4, 2))
    
    # Equipment and qualifications
    equipment_required = Column(JSON)  # List of required instruments
    analyst_qualifications = Column(JSON)  # Required training/certifications
    environmental_requirements = Column(JSON)  # Temperature, humidity, etc.
    
    # Validation and approval
    validation_status = Column(String(50), default="draft")
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(DateTime)
    effective_date = Column(DateTime)
    retirement_date = Column(DateTime)
    
    # Relationships
    procedure_document = relationship("Document", foreign_keys=[procedure_document_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    test_specifications = relationship("TestSpecification", back_populates="test_method")
    test_executions = relationship("TestExecution", back_populates="test_method")
    
    def __repr__(self):
        return f"<TestMethod {self.method_code}: {self.title}>"


class TestSpecification(BaseModel):
    """Acceptance criteria and limits for test methods"""
    __tablename__ = "test_specifications"
    
    id = Column(Integer, primary_key=True, index=True)
    sample_type_id = Column(Integer, ForeignKey("sample_types.id"), nullable=False)
    test_method_id = Column(Integer, ForeignKey("test_methods.id"), nullable=False)
    
    # Specification details
    parameter_name = Column(String(200), nullable=False)
    specification_type = Column(String(50))  # limit, range, identity, etc.
    lower_limit = Column(Numeric(15, 6))
    upper_limit = Column(Numeric(15, 6))
    target_value = Column(Numeric(15, 6))
    units = Column(String(50))
    
    # Regulatory and compliance
    regulatory_requirement = Column(Boolean, default=False)
    criticality_level = Column(String(20), default="normal")
    statistical_approach = Column(String(100))  # n=1, mean of 3, etc.
    
    # Approval and versioning
    version = Column(String(20), default="1.0")
    effective_date = Column(DateTime, default=func.now())
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    sample_type = relationship("SampleType", back_populates="test_specifications")
    test_method = relationship("TestMethod", back_populates="test_specifications")
    approved_by = relationship("User")
    
    def __repr__(self):
        return f"<TestSpecification {self.parameter_name}: {self.lower_limit}-{self.upper_limit}>"


class Instrument(BaseModel):
    """Laboratory equipment and instrumentation registry"""
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Equipment details
    manufacturer = Column(String(200))
    model = Column(String(100))
    serial_number = Column(String(100))
    asset_number = Column(String(100))
    purchase_date = Column(Date)
    warranty_expiry = Column(Date)
    
    # Location and status
    location = Column(String(200))
    department = Column(String(100))
    status = Column(Enum(InstrumentStatus), default=InstrumentStatus.QUALIFIED)
    
    # Calibration and maintenance
    calibration_frequency_days = Column(Integer, default=365)
    last_calibration_date = Column(Date)
    next_calibration_due = Column(Date)
    maintenance_frequency_days = Column(Integer, default=90)
    last_maintenance_date = Column(Date)
    next_maintenance_due = Column(Date)
    
    # Technical specifications
    specifications = Column(JSON)  # Technical specs and capabilities
    operating_ranges = Column(JSON)  # Temperature, humidity, etc.
    
    # Relationships
    calibration_records = relationship("CalibrationRecord", back_populates="instrument")
    test_executions = relationship("TestExecution", back_populates="instrument")
    
    def __repr__(self):
        return f"<Instrument {self.instrument_id}: {self.name}>"


class TestExecution(BaseModel):
    """Individual test run tracking and execution"""
    __tablename__ = "test_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(50), unique=True, nullable=False, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False)
    test_method_id = Column(Integer, ForeignKey("test_methods.id"), nullable=False)
    
    # Execution details
    analyst_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    completion_datetime = Column(DateTime)
    status = Column(Enum(TestStatus), default=TestStatus.PENDING)
    
    # Environmental and equipment
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    environmental_conditions = Column(JSON)  # Temperature, humidity at test time
    reagent_lot_numbers = Column(JSON)  # Reagents and reference standards used
    
    # Review and approval
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    review_date = Column(DateTime)
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(DateTime)
    
    # Notes and deviations
    analyst_notes = Column(Text)
    deviations = Column(JSON)  # Any deviations from standard method
    
    # Relationships
    sample = relationship("Sample", back_populates="test_executions")
    test_method = relationship("TestMethod", back_populates="test_executions")
    analyst = relationship("User", foreign_keys=[analyst_id])
    instrument = relationship("Instrument", back_populates="test_executions")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    test_results = relationship("TestResult", back_populates="test_execution")
    
    def __repr__(self):
        return f"<TestExecution {self.execution_id}: {self.sample.sample_id}>"


class TestResult(BaseModel):
    """Individual test result data with compliance checking"""
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=False)
    test_specification_id = Column(Integer, ForeignKey("test_specifications.id"), nullable=False)
    
    # Result data
    parameter_name = Column(String(200), nullable=False)
    result_value = Column(Numeric(15, 6))
    result_text = Column(Text)  # For qualitative results
    units = Column(String(50))
    
    # Quality assessment
    pass_fail = Column(Boolean)
    out_of_specification = Column(Boolean, default=False)
    deviation_percent = Column(Numeric(8, 3))  # % deviation from target
    
    # Statistical data (for multiple measurements)
    replicate_values = Column(JSON)  # Individual replicate measurements
    mean_value = Column(Numeric(15, 6))
    standard_deviation = Column(Numeric(15, 6))
    relative_standard_deviation = Column(Numeric(8, 3))
    
    # Data integrity
    raw_data_file = Column(String(500))  # Path to raw instrument data
    data_hash = Column(String(128))  # Hash for data integrity verification
    electronic_signature = Column(JSON)  # Digital signature data
    
    # Review and approval
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    review_date = Column(DateTime)
    review_comments = Column(Text)
    
    # Relationships
    test_execution = relationship("TestExecution", back_populates="test_results")
    test_specification = relationship("TestSpecification")
    reviewed_by = relationship("User")
    
    def __repr__(self):
        return f"<TestResult {self.parameter_name}: {self.result_value} {self.units}>"


class CalibrationRecord(BaseModel):
    """Instrument calibration tracking and compliance"""
    __tablename__ = "calibration_records"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    calibration_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Calibration details
    calibration_date = Column(Date, nullable=False)
    next_due_date = Column(Date, nullable=False)
    calibration_type = Column(String(100))  # Annual, quarterly, etc.
    
    # Standards and references
    calibration_standard = Column(String(200))
    standard_certificate = Column(String(200))
    standard_expiry_date = Column(Date)
    reference_values = Column(JSON)  # Expected vs actual values
    
    # Calibration results
    calibration_results = Column(JSON)  # Detailed calibration data
    accuracy_check = Column(Boolean)
    precision_check = Column(Boolean)
    linearity_check = Column(Boolean)
    overall_result = Column(String(20))  # PASS/FAIL
    
    # Personnel and approval
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    witnessed_by_id = Column(Integer, ForeignKey("users.id"))
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(DateTime)
    
    # Documentation
    certificate_reference = Column(String(200))
    calibration_report_path = Column(String(500))
    comments = Column(Text)
    
    # Relationships
    instrument = relationship("Instrument", back_populates="calibration_records")
    performed_by = relationship("User", foreign_keys=[performed_by_id])
    witnessed_by = relationship("User", foreign_keys=[witnessed_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f"<CalibrationRecord {self.calibration_id}: {self.instrument.name}>"


class LIMSAuditLog(BaseModel):
    """Specialized audit log for LIMS data integrity"""
    __tablename__ = "lims_audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)  # Sample, TestResult, etc.
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, APPROVE
    
    # Audit details
    old_values = Column(JSON)
    new_values = Column(JSON)
    change_reason = Column(Text)
    
    # User and system info
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(128))
    
    # Timestamps
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<LIMSAuditLog {self.entity_type}:{self.entity_id} {self.action}>"