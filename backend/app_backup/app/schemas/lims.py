"""
Laboratory Information Management System (LIMS) Schemas
Phase 5 Implementation - QMS Platform v3.0

Pydantic schemas for API request/response validation
and data serialization for the LIMS module.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum

from app.models.lims import (
    SampleCategory, SampleStatus, TestStatus, InstrumentStatus
)


# Base Schemas for Common Patterns
class LIMSBaseModel(BaseModel):
    """Base model for LIMS schemas with common configurations"""
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# Sample Type Schemas
class SampleTypeBase(LIMSBaseModel):
    code: str = Field(..., max_length=50, description="Unique sample type code")
    name: str = Field(..., max_length=200, description="Sample type name")
    category: SampleCategory = Field(..., description="Sample category")
    description: Optional[str] = Field(None, description="Detailed description")
    storage_temperature_min: Optional[float] = Field(None, description="Min storage temp (°C)")
    storage_temperature_max: Optional[float] = Field(None, description="Max storage temp (°C)")
    storage_humidity_max: Optional[float] = Field(None, description="Max humidity (%)")
    storage_conditions: Optional[str] = Field(None, description="Storage requirements")
    shelf_life_days: Optional[int] = Field(None, ge=1, description="Shelf life in days")
    hazard_classification: Optional[str] = Field(None, description="Safety classification")
    regulatory_category: Optional[str] = Field(None, description="Regulatory category")
    disposal_instructions: Optional[str] = Field(None, description="Disposal procedures")


class SampleTypeCreate(SampleTypeBase):
    pass


class SampleTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    storage_temperature_min: Optional[float] = None
    storage_temperature_max: Optional[float] = None
    storage_humidity_max: Optional[float] = None
    storage_conditions: Optional[str] = None
    shelf_life_days: Optional[int] = Field(None, ge=1)
    hazard_classification: Optional[str] = None
    regulatory_category: Optional[str] = None
    disposal_instructions: Optional[str] = None


class SampleType(SampleTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime


# Sample Schemas
class SampleBase(LIMSBaseModel):
    sample_id: str = Field(..., max_length=50, description="Unique sample identifier")
    batch_lot_number: str = Field(..., max_length=100, description="Batch or lot number")
    supplier_reference: Optional[str] = Field(None, max_length=100, description="Supplier reference")
    internal_reference: Optional[str] = Field(None, max_length=100, description="Internal reference")
    collection_date: datetime = Field(..., description="Sample collection date/time")
    expiry_date: Optional[datetime] = Field(None, description="Sample expiry date")
    quantity: Optional[float] = Field(None, ge=0, description="Sample quantity")
    quantity_units: Optional[str] = Field(None, max_length=20, description="Quantity units")
    storage_location: Optional[str] = Field(None, max_length=200, description="Storage location")
    collected_by: Optional[str] = Field(None, max_length=200, description="Person who collected sample")
    temperature_on_receipt: Optional[float] = Field(None, description="Temperature on receipt (°C)")
    condition_on_receipt: Optional[str] = Field(None, description="Condition on receipt")
    priority_level: Optional[str] = Field("normal", pattern="^(normal|high|urgent)$", description="Priority level")
    special_instructions: Optional[str] = Field(None, description="Special handling instructions")

    @validator('expiry_date')
    def expiry_after_collection(cls, v, values):
        if v and 'collection_date' in values and v <= values['collection_date']:
            raise ValueError('Expiry date must be after collection date')
        return v


class SampleCreate(SampleBase):
    sample_type_id: int = Field(..., description="Sample type ID")
    received_by_id: Optional[int] = Field(None, description="User who received the sample")


class SampleUpdate(BaseModel):
    batch_lot_number: Optional[str] = Field(None, max_length=100)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    internal_reference: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    quantity: Optional[float] = Field(None, ge=0)
    quantity_units: Optional[str] = Field(None, max_length=20)
    storage_location: Optional[str] = Field(None, max_length=200)
    status: Optional[SampleStatus] = None
    temperature_on_receipt: Optional[float] = None
    condition_on_receipt: Optional[str] = None
    priority_level: Optional[str] = Field(None, pattern="^(normal|high|urgent)$")
    special_instructions: Optional[str] = None
    current_custodian_id: Optional[int] = Field(None, description="Current custodian user ID")


class Sample(SampleBase):
    id: int
    sample_type_id: int
    received_date: datetime
    status: SampleStatus
    received_by_id: Optional[int]
    current_custodian_id: Optional[int]
    chain_of_custody: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships (optional for performance)
    sample_type: Optional[SampleType] = None


# Test Method Schemas
class TestMethodBase(LIMSBaseModel):
    method_code: str = Field(..., max_length=50, description="Unique method code")
    title: str = Field(..., max_length=200, description="Method title")
    version: str = Field(..., max_length=20, description="Method version")
    description: Optional[str] = Field(None, description="Method description")
    method_type: Optional[str] = Field(None, max_length=100, description="Method type (HPLC, GC, etc.)")
    estimated_duration_hours: Optional[float] = Field(None, ge=0, description="Estimated duration")
    equipment_required: Optional[List[str]] = Field(None, description="Required equipment list")
    analyst_qualifications: Optional[List[str]] = Field(None, description="Required qualifications")
    environmental_requirements: Optional[Dict[str, Any]] = Field(None, description="Environmental conditions")
    validation_status: Optional[str] = Field("draft", description="Validation status")
    effective_date: Optional[datetime] = Field(None, description="Effective date")
    retirement_date: Optional[datetime] = Field(None, description="Retirement date")


class TestMethodCreate(TestMethodBase):
    procedure_document_id: Optional[int] = Field(None, description="Reference to EDMS document")


class TestMethodUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    method_type: Optional[str] = Field(None, max_length=100)
    estimated_duration_hours: Optional[float] = Field(None, ge=0)
    equipment_required: Optional[List[str]] = None
    analyst_qualifications: Optional[List[str]] = None
    environmental_requirements: Optional[Dict[str, Any]] = None
    validation_status: Optional[str] = None
    retirement_date: Optional[datetime] = None
    procedure_document_id: Optional[int] = None


class TestMethod(TestMethodBase):
    id: int
    procedure_document_id: Optional[int]
    approved_by_id: Optional[int]
    approval_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Test Specification Schemas
class TestSpecificationBase(LIMSBaseModel):
    parameter_name: str = Field(..., max_length=200, description="Parameter name")
    specification_type: Optional[str] = Field(None, max_length=50, description="Specification type")
    lower_limit: Optional[float] = Field(None, description="Lower specification limit")
    upper_limit: Optional[float] = Field(None, description="Upper specification limit")
    target_value: Optional[float] = Field(None, description="Target value")
    units: Optional[str] = Field(None, max_length=50, description="Units of measurement")
    regulatory_requirement: bool = Field(False, description="Is regulatory requirement")
    criticality_level: Optional[str] = Field("normal", description="Criticality level")
    statistical_approach: Optional[str] = Field(None, description="Statistical approach")
    version: str = Field("1.0", description="Specification version")

    @validator('upper_limit')
    def upper_greater_than_lower(cls, v, values):
        if v and 'lower_limit' in values and values['lower_limit'] and v <= values['lower_limit']:
            raise ValueError('Upper limit must be greater than lower limit')
        return v


class TestSpecificationCreate(TestSpecificationBase):
    sample_type_id: int = Field(..., description="Sample type ID")
    test_method_id: int = Field(..., description="Test method ID")


class TestSpecificationUpdate(BaseModel):
    parameter_name: Optional[str] = Field(None, max_length=200)
    specification_type: Optional[str] = Field(None, max_length=50)
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    target_value: Optional[float] = None
    units: Optional[str] = Field(None, max_length=50)
    regulatory_requirement: Optional[bool] = None
    criticality_level: Optional[str] = None
    statistical_approach: Optional[str] = None


class TestSpecification(TestSpecificationBase):
    id: int
    sample_type_id: int
    test_method_id: int
    effective_date: datetime
    approved_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# Instrument Schemas
class InstrumentBase(LIMSBaseModel):
    instrument_id: str = Field(..., max_length=50, description="Unique instrument ID")
    name: str = Field(..., max_length=200, description="Instrument name")
    manufacturer: Optional[str] = Field(None, max_length=200, description="Manufacturer")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    asset_number: Optional[str] = Field(None, max_length=100, description="Asset number")
    purchase_date: Optional[date] = Field(None, description="Purchase date")
    warranty_expiry: Optional[date] = Field(None, description="Warranty expiry")
    location: Optional[str] = Field(None, max_length=200, description="Physical location")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    calibration_frequency_days: int = Field(365, ge=1, description="Calibration frequency")
    maintenance_frequency_days: int = Field(90, ge=1, description="Maintenance frequency")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Technical specifications")
    operating_ranges: Optional[Dict[str, Any]] = Field(None, description="Operating ranges")


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    manufacturer: Optional[str] = Field(None, max_length=200)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    asset_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    status: Optional[InstrumentStatus] = None
    calibration_frequency_days: Optional[int] = Field(None, ge=1)
    maintenance_frequency_days: Optional[int] = Field(None, ge=1)
    last_calibration_date: Optional[date] = None
    next_calibration_due: Optional[date] = None
    specifications: Optional[Dict[str, Any]] = None
    operating_ranges: Optional[Dict[str, Any]] = None


class Instrument(InstrumentBase):
    id: int
    status: InstrumentStatus
    last_calibration_date: Optional[date]
    next_calibration_due: Optional[date]
    last_maintenance_date: Optional[date]
    next_maintenance_due: Optional[date]
    created_at: datetime
    updated_at: datetime

# Test Execution Schemas
class TestExecutionBase(LIMSBaseModel):
    execution_id: str = Field(..., max_length=50, description="Unique execution ID")
    start_datetime: datetime = Field(..., description="Test start date/time")
    environmental_conditions: Optional[Dict[str, Any]] = Field(None, description="Environmental conditions")
    reagent_lot_numbers: Optional[Dict[str, str]] = Field(None, description="Reagent lot numbers used")
    analyst_notes: Optional[str] = Field(None, description="Analyst notes and observations")
    deviations: Optional[List[Dict[str, Any]]] = Field(None, description="Method deviations")
