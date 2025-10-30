# QMS Department Hierarchy Schemas - Phase A Sprint 2
# Pydantic schemas for department hierarchy and organization management

from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DepartmentType(str, Enum):
    """Department type enumeration"""
    OPERATIONAL = "operational"
    ADMINISTRATIVE = "administrative"
    QUALITY = "quality"
    RESEARCH = "research"
    REGULATORY = "regulatory"


class OrganizationType(str, Enum):
    """Organization type enumeration"""
    MANUFACTURING = "manufacturing"
    LABORATORY = "laboratory"
    CORPORATE = "corporate"
    SUBSIDIARY = "subsidiary"


class RegulatoryRegion(str, Enum):
    """Regulatory region enumeration"""
    FDA = "FDA"  # US Food and Drug Administration
    EMA = "EMA"  # European Medicines Agency
    PMDA = "PMDA"  # Japan Pharmaceuticals and Medical Devices Agency
    HEALTH_CANADA = "Health Canada"
    TGA = "TGA"  # Australia Therapeutic Goods Administration
    NMPA = "NMPA"  # China National Medical Products Administration


# Department Schemas
class DepartmentBase(BaseModel):
    """Base department schema"""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    description: Optional[str] = None
    parent_department_id: Optional[int] = None
    department_head_id: Optional[int] = None
    cost_center: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    department_type: Optional[DepartmentType] = DepartmentType.OPERATIONAL
    
    @validator('code')
    def validate_code(cls, v):
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Department code can only contain letters, numbers, hyphens, and underscores')
        return v.upper() if v else v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Department name cannot be empty')
        return v.strip()


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department"""
    organization_id: int = Field(..., gt=0)
    code: str = Field(..., min_length=2, max_length=20)


class DepartmentUpdate(DepartmentBase):
    """Schema for updating a department"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class DepartmentResponse(DepartmentBase):
    """Schema for department response"""
    id: int
    organization_id: int
    hierarchy_level: int
    hierarchy_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    # Related data
    organization_name: Optional[str] = None
    parent_department_name: Optional[str] = None
    department_head: Optional[Dict[str, Any]] = None
    direct_user_count: int = 0
    child_department_count: int = 0
    
    class Config:
        from_attributes = True


class DepartmentHierarchyNode(BaseModel):
    """Schema for department hierarchy tree node"""
    id: int
    name: str
    code: Optional[str] = None
    department_type: Optional[str] = None
    location: Optional[str] = None
    hierarchy_level: int
    hierarchy_path: Optional[str] = None
    user_count: int = 0
    department_head: Optional[Dict[str, Any]] = None
    children: List['DepartmentHierarchyNode'] = []
    
    class Config:
        from_attributes = True


# Department Role Assignment Schemas
class DepartmentRoleAssignmentRequest(BaseModel):
    """Schema for department role assignment request"""
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    comment: Optional[str] = None
    
    @validator('valid_until')
    def validate_dates(cls, v, values):
        if v and 'valid_from' in values and values['valid_from']:
            if v <= values['valid_from']:
                raise ValueError('valid_until must be after valid_from')
        return v


class DepartmentRoleResponse(BaseModel):
    """Schema for department role assignment response"""
    id: int
    department_id: int
    role_id: int
    user_id: int
    assigned_by: Optional[int] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    
    # Related data
    department_name: Optional[str] = None
    role_name: Optional[str] = None
    user_name: Optional[str] = None
    assigned_by_name: Optional[str] = None
    days_until_expiry: Optional[int] = None
    
    class Config:
        from_attributes = True


# Organization Schemas
class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    organization_type: Optional[OrganizationType] = OrganizationType.MANUFACTURING
    parent_organization_id: Optional[int] = None
    regulatory_region: Optional[RegulatoryRegion] = None
    regulatory_license: Optional[str] = Field(None, max_length=100)
    
    @validator('code')
    def validate_code(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Organization code can only contain letters, numbers, hyphens, and underscores')
        return v.upper()
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            return f'https://{v}'
        return v


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""
    pass


class OrganizationUpdate(OrganizationBase):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    # Related data
    parent_organization_name: Optional[str] = None
    total_departments: int = 0
    total_users: int = 0
    child_organizations: List['OrganizationResponse'] = []
    
    class Config:
        from_attributes = True


# Analytics Schemas
class DepartmentAnalytics(BaseModel):
    """Schema for department analytics and metrics"""
    department_id: int
    department_name: str
    hierarchy_level: int
    direct_users: int
    total_users: int  # Including child departments
    child_departments: int
    role_distribution: Dict[str, int] = {}
    recent_logins_30d: int = 0
    average_session_duration_minutes: Optional[float] = None
    department_head: Optional[Dict[str, Any]] = None
    cost_center: Optional[str] = None
    location: Optional[str] = None
    department_type: Optional[str] = None
    
    # Activity metrics
    most_active_users: List[Dict[str, Any]] = []
    least_active_users: List[Dict[str, Any]] = []
    training_completion_rate: Optional[float] = None
    quality_events_count: int = 0


class OrganizationAnalytics(BaseModel):
    """Schema for organization-wide analytics"""
    organization_id: int
    organization_name: str
    total_departments: int
    max_hierarchy_depth: int
    department_type_distribution: Dict[str, int] = {}
    user_distribution_by_level: Dict[str, int] = {}
    total_users: int
    active_users_30d: int
    
    # Performance metrics
    average_training_completion_rate: Optional[float] = None
    total_quality_events: int = 0
    total_active_sessions: int = 0
    departments_without_heads: int = 0
    
    # Geographic distribution
    location_distribution: Dict[str, int] = {}
    
    # Regulatory compliance
    regulatory_region: Optional[str] = None
    departments_by_type: Dict[str, List[Dict[str, Any]]] = {}


class BulkDepartmentOperationRequest(BaseModel):
    """Schema for bulk department operations"""
    department_ids: List[int] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., pattern="^(activate|deactivate|move|assign_head)$")
    parameters: Dict[str, Any] = {}
    
    @validator('department_ids')
    def validate_department_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Department IDs must be unique')
        return v


class DepartmentMoveRequest(BaseModel):
    """Schema for moving department to new parent"""
    new_parent_id: Optional[int] = None
    preserve_hierarchy: bool = True
    update_permissions: bool = True


class DepartmentSearchRequest(BaseModel):
    """Schema for department search and filtering"""
    organization_id: Optional[int] = None
    department_type: Optional[DepartmentType] = None
    location: Optional[str] = None
    hierarchy_level: Optional[int] = Field(None, ge=0, le=10)
    has_department_head: Optional[bool] = None
    min_user_count: Optional[int] = Field(None, ge=0)
    max_user_count: Optional[int] = Field(None, ge=0)
    search_term: Optional[str] = Field(None, min_length=2, max_length=100)
    
    @validator('max_user_count')
    def validate_user_counts(cls, v, values):
        if v is not None and 'min_user_count' in values and values['min_user_count'] is not None:
            if v < values['min_user_count']:
                raise ValueError('max_user_count must be greater than or equal to min_user_count')
        return v


# Forward reference resolution
DepartmentHierarchyNode.model_rebuild()
OrganizationResponse.model_rebuild()