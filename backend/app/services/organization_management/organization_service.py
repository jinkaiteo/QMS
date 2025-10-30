# QMS Organization Service - Phase A Sprint 2
# Service layer for organization and department hierarchy management

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from app.models.user import User
from app.models.organization_management.department_hierarchy import Department, DepartmentRole, Organization
from app.models.user import Role
from app.schemas.organization_management.department_hierarchy import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentHierarchyNode,
    DepartmentRoleAssignmentRequest, DepartmentRoleResponse,
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    DepartmentMoveRequest, BulkDepartmentOperationRequest, DepartmentSearchRequest
)
from app.core.security import audit_logger
from app.core.exceptions import AuthorizationException


class OrganizationService:
    """Service for managing organizations and department hierarchies"""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    # Department Hierarchy Management
    def get_department_hierarchy_tree(self, organization_id: Optional[int] = None, 
                                    department_id: Optional[int] = None) -> List[DepartmentHierarchyNode]:
        """Get complete department hierarchy as nested tree structure"""
        if not self.current_user.has_permission("organization.view", "core"):
            raise AuthorizationException("Insufficient permissions to view organization structure")
        
        # Build base query
        query = self.db.query(Department).options(
            joinedload(Department.department_head),
            joinedload(Department.child_departments),
            joinedload(Department.users)
        )
        
        if department_id:
            # Get specific department and its descendants
            department = query.filter(Department.id == department_id).first()
            if not department:
                raise HTTPException(status_code=404, detail="Department not found")
            return [self._build_department_tree_node(department)]
        
        # Get root departments (no parent)
        query = query.filter(Department.parent_department_id.is_(None))
        
        if organization_id:
            query = query.filter(Department.organization_id == organization_id)
        elif self.current_user.organization_id:
            # Limit to user's organization if not admin
            query = query.filter(Department.organization_id == self.current_user.organization_id)
        
        root_departments = query.order_by(Department.name).all()
        
        return [self._build_department_tree_node(dept) for dept in root_departments]
    
    def create_department(self, dept_data: DepartmentCreate) -> DepartmentResponse:
        """Create new department with hierarchy support"""
        if not self.current_user.has_permission("organization.manage", "core"):
            raise AuthorizationException("Insufficient permissions to create departments")
        
        # Validate organization exists and user has access
        organization = self.db.query(Organization).filter(
            Organization.id == dept_data.organization_id,
            Organization.is_active == True
        ).first()
        
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Validate department code uniqueness
        if dept_data.code:
            existing_dept = self.db.query(Department).filter(
                Department.code == dept_data.code,
                Department.is_active == True
            ).first()
            
            if existing_dept:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Department code '{dept_data.code}' already exists"
                )
        
        # Validate parent department if specified
        parent_department = None
        if dept_data.parent_department_id:
            parent_department = self.db.query(Department).filter(
                Department.id == dept_data.parent_department_id,
                Department.organization_id == dept_data.organization_id,
                Department.is_active == True
            ).first()
            
            if not parent_department:
                raise HTTPException(
                    status_code=404, 
                    detail="Parent department not found or not in same organization"
                )
        
        # Validate department head if specified
        if dept_data.department_head_id:
            dept_head = self.db.query(User).filter(
                User.id == dept_data.department_head_id,
                User.is_active == True
            ).first()
            
            if not dept_head:
                raise HTTPException(status_code=404, detail="Department head user not found")
        
        # Calculate hierarchy level and path
        hierarchy_level = 0
        hierarchy_path = ""
        
        if parent_department:
            hierarchy_level = parent_department.hierarchy_level + 1
            if parent_department.hierarchy_path:
                hierarchy_path = f"{parent_department.hierarchy_path}.{parent_department.id}"
            else:
                hierarchy_path = str(parent_department.id)
        
        # Create department
        department = Department(
            organization_id=dept_data.organization_id,
            name=dept_data.name,
            code=dept_data.code,
            description=dept_data.description,
            parent_department_id=dept_data.parent_department_id,
            department_head_id=dept_data.department_head_id,
            cost_center=dept_data.cost_center,
            location=dept_data.location,
            department_type=dept_data.department_type,
            hierarchy_level=hierarchy_level,
            hierarchy_path=hierarchy_path
        )
        
        self.db.add(department)
        self.db.commit()
        
        # Log department creation
        audit_logger.log_organization_event(
            admin_user_id=self.current_user.id,
            event_type="department_created",
            details={
                "department_id": department.id,
                "department_name": department.name,
                "organization_id": dept_data.organization_id,
                "parent_department_id": dept_data.parent_department_id,
                "hierarchy_level": hierarchy_level
            }
        )
        
        return self._convert_to_department_response(department)
    
    def update_department(self, department_id: int, dept_data: DepartmentUpdate) -> DepartmentResponse:
        """Update department information"""
        if not self.current_user.has_permission("organization.manage", "core"):
            raise AuthorizationException("Insufficient permissions to update departments")
        
        department = self.db.query(Department).filter(
            Department.id == department_id,
            Department.is_active == True
        ).first()
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Store original values for audit
        original_values = {
            "name": department.name,
            "parent_department_id": department.parent_department_id,
            "department_head_id": department.department_head_id
        }
        
        # Update fields
        update_fields = dept_data.dict(exclude_unset=True)
        for field, value in update_fields.items():
            if hasattr(department, field):
                setattr(department, field, value)
        
        # If parent changed, recalculate hierarchy
        if "parent_department_id" in update_fields:
            self._recalculate_hierarchy(department)
        
        department.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Log department update
        audit_logger.log_organization_event(
            admin_user_id=self.current_user.id,
            event_type="department_updated",
            details={
                "department_id": department_id,
                "original_values": original_values,
                "updated_fields": update_fields
            }
        )
        
        return self._convert_to_department_response(department)
    
    def move_department(self, department_id: int, move_request: DepartmentMoveRequest) -> DepartmentResponse:
        """Move department to new parent with hierarchy recalculation"""
        if not self.current_user.has_permission("organization.manage", "core"):
            raise AuthorizationException("Insufficient permissions to move departments")
        
        department = self.db.query(Department).filter(
            Department.id == department_id,
            Department.is_active == True
        ).first()
        
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Validate new parent if specified
        if move_request.new_parent_id:
            new_parent = self.db.query(Department).filter(
                Department.id == move_request.new_parent_id,
                Department.organization_id == department.organization_id,
                Department.is_active == True
            ).first()
            
            if not new_parent:
                raise HTTPException(status_code=404, detail="New parent department not found")
            
            # Prevent circular references
            if self._would_create_cycle(department_id, move_request.new_parent_id):
                raise HTTPException(
                    status_code=400, 
                    detail="Moving department would create circular reference"
                )
        
        old_parent_id = department.parent_department_id
        department.parent_department_id = move_request.new_parent_id
        
        # Recalculate hierarchy for moved department and all descendants
        self._recalculate_hierarchy(department)
        
        if move_request.preserve_hierarchy:
            # Update all descendants
            descendants = department.get_all_descendants()
            for desc in descendants:
                self._recalculate_hierarchy(desc)
        
        self.db.commit()
        
        # Log department move
        audit_logger.log_organization_event(
            admin_user_id=self.current_user.id,
            event_type="department_moved",
            details={
                "department_id": department_id,
                "old_parent_id": old_parent_id,
                "new_parent_id": move_request.new_parent_id,
                "preserve_hierarchy": move_request.preserve_hierarchy
            }
        )
        
        return self._convert_to_department_response(department)
    
    # Department Role Management
    def assign_department_role(self, user_id: int, department_id: int, role_id: int,
                             assignment_data: DepartmentRoleAssignmentRequest) -> DepartmentRoleResponse:
        """Assign role to user in specific department"""
        if not self.current_user.has_permission("user.manage_roles", "core"):
            raise AuthorizationException("Insufficient permissions to assign roles")
        
        # Validate entities exist
        user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        department = self.db.query(Department).filter(
            Department.id == department_id, 
            Department.is_active == True
        ).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        role = self.db.query(Role).filter(Role.id == role_id, Role.is_active == True).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Check if assignment already exists
        existing = self.db.query(DepartmentRole).filter(
            DepartmentRole.user_id == user_id,
            DepartmentRole.department_id == department_id,
            DepartmentRole.role_id == role_id,
            DepartmentRole.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Role already assigned to user in this department"
            )
        
        # Create assignment
        dept_role = DepartmentRole(
            user_id=user_id,
            department_id=department_id,
            role_id=role_id,
            assigned_by=self.current_user.id,
            valid_from=assignment_data.valid_from or datetime.utcnow(),
            valid_until=assignment_data.valid_until
        )
        
        self.db.add(dept_role)
        self.db.commit()
        
        # Log role assignment
        audit_logger.log_user_management_event(
            admin_user_id=self.current_user.id,
            target_user_id=user_id,
            event_type="department_role_assigned",
            details={
                "department_id": department_id,
                "role_id": role_id,
                "valid_from": dept_role.valid_from.isoformat(),
                "valid_until": dept_role.valid_until.isoformat() if dept_role.valid_until else None,
                "comment": assignment_data.comment
            }
        )
        
        return self._convert_to_department_role_response(dept_role)
    
    def revoke_department_role(self, department_role_id: int) -> Dict[str, str]:
        """Revoke department role assignment"""
        if not self.current_user.has_permission("user.manage_roles", "core"):
            raise AuthorizationException("Insufficient permissions to revoke roles")
        
        dept_role = self.db.query(DepartmentRole).filter(
            DepartmentRole.id == department_role_id,
            DepartmentRole.is_active == True
        ).first()
        
        if not dept_role:
            raise HTTPException(status_code=404, detail="Department role assignment not found")
        
        # Deactivate role assignment
        dept_role.is_active = False
        dept_role.valid_until = datetime.utcnow()
        dept_role.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Log role revocation
        audit_logger.log_user_management_event(
            admin_user_id=self.current_user.id,
            target_user_id=dept_role.user_id,
            event_type="department_role_revoked",
            details={
                "department_role_id": department_role_id,
                "department_id": dept_role.department_id,
                "role_id": dept_role.role_id
            }
        )
        
        return {"message": "Department role assignment revoked successfully"}
    
    def get_user_effective_permissions(self, user_id: int, department_id: Optional[int] = None) -> List[str]:
        """Calculate user's effective permissions considering department hierarchy"""
        user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        permissions = set()
        
        # Get global role permissions
        for user_role in user.user_roles:
            if user_role.is_active and user_role.role.is_active:
                permissions.update(user_role.role.permissions or [])
        
        # Get department-specific permissions
        dept_roles_query = self.db.query(DepartmentRole).filter(
            DepartmentRole.user_id == user_id,
            DepartmentRole.is_active == True
        )
        
        if department_id:
            # Include roles in the specific department and its ancestors
            department = self.db.query(Department).filter(Department.id == department_id).first()
            if department:
                ancestor_ids = [ancestor.id for ancestor in department.get_all_ancestors()]
                ancestor_ids.append(department_id)
                dept_roles_query = dept_roles_query.filter(
                    DepartmentRole.department_id.in_(ancestor_ids)
                )
        
        dept_roles = dept_roles_query.all()
        
        for dept_role in dept_roles:
            if dept_role.is_valid:
                permissions.update(dept_role.role.permissions or [])
        
        return sorted(list(permissions))
    
    def search_departments(self, search_request: DepartmentSearchRequest) -> List[DepartmentResponse]:
        """Search and filter departments based on criteria"""
        if not self.current_user.has_permission("organization.view", "core"):
            raise AuthorizationException("Insufficient permissions to search departments")
        
        query = self.db.query(Department).filter(Department.is_active == True)
        
        # Apply filters
        if search_request.organization_id:
            query = query.filter(Department.organization_id == search_request.organization_id)
        
        if search_request.department_type:
            query = query.filter(Department.department_type == search_request.department_type)
        
        if search_request.location:
            query = query.filter(Department.location.ilike(f"%{search_request.location}%"))
        
        if search_request.hierarchy_level is not None:
            query = query.filter(Department.hierarchy_level == search_request.hierarchy_level)
        
        if search_request.has_department_head is not None:
            if search_request.has_department_head:
                query = query.filter(Department.department_head_id.isnot(None))
            else:
                query = query.filter(Department.department_head_id.is_(None))
        
        if search_request.search_term:
            search_term = f"%{search_request.search_term}%"
            query = query.filter(
                or_(
                    Department.name.ilike(search_term),
                    Department.code.ilike(search_term),
                    Department.description.ilike(search_term)
                )
            )
        
        departments = query.order_by(Department.hierarchy_level, Department.name).all()
        
        # Filter by user count if specified
        if search_request.min_user_count is not None or search_request.max_user_count is not None:
            filtered_depts = []
            for dept in departments:
                user_count = len(dept.users)
                if search_request.min_user_count is not None and user_count < search_request.min_user_count:
                    continue
                if search_request.max_user_count is not None and user_count > search_request.max_user_count:
                    continue
                filtered_depts.append(dept)
            departments = filtered_depts
        
        return [self._convert_to_department_response(dept) for dept in departments]
    
    # Helper Methods
    def _build_department_tree_node(self, department: Department) -> DepartmentHierarchyNode:
        """Build department tree node with children"""
        return DepartmentHierarchyNode(
            id=department.id,
            name=department.name,
            code=department.code,
            department_type=department.department_type,
            location=department.location,
            hierarchy_level=department.hierarchy_level,
            hierarchy_path=department.hierarchy_path,
            user_count=len(department.users),
            department_head={
                "id": department.department_head.id,
                "full_name": department.department_head.full_name,
                "job_title": department.department_head.job_title,
                "profile_picture_url": department.department_head.profile_picture_url
            } if department.department_head else None,
            children=[self._build_department_tree_node(child) for child in department.child_departments]
        )
    
    def _convert_to_department_response(self, department: Department) -> DepartmentResponse:
        """Convert Department model to response schema"""
        return DepartmentResponse(
            id=department.id,
            organization_id=department.organization_id,
            name=department.name,
            code=department.code,
            description=department.description,
            parent_department_id=department.parent_department_id,
            department_head_id=department.department_head_id,
            cost_center=department.cost_center,
            location=department.location,
            department_type=department.department_type,
            hierarchy_level=department.hierarchy_level,
            hierarchy_path=department.hierarchy_path,
            created_at=department.created_at,
            updated_at=department.updated_at,
            is_active=department.is_active,
            organization_name=department.organization.name if department.organization else None,
            parent_department_name=department.parent_department.name if department.parent_department else None,
            department_head={
                "id": department.department_head.id,
                "full_name": department.department_head.full_name,
                "job_title": department.department_head.job_title
            } if department.department_head else None,
            direct_user_count=len(department.users),
            child_department_count=len(department.child_departments)
        )
    
    def _convert_to_department_role_response(self, dept_role: DepartmentRole) -> DepartmentRoleResponse:
        """Convert DepartmentRole model to response schema"""
        return DepartmentRoleResponse(
            id=dept_role.id,
            department_id=dept_role.department_id,
            role_id=dept_role.role_id,
            user_id=dept_role.user_id,
            assigned_by=dept_role.assigned_by,
            valid_from=dept_role.valid_from,
            valid_until=dept_role.valid_until,
            is_active=dept_role.is_active,
            created_at=dept_role.created_at,
            department_name=dept_role.department.name if dept_role.department else None,
            role_name=dept_role.role.display_name if dept_role.role else None,
            user_name=dept_role.user.full_name if dept_role.user else None,
            assigned_by_name=dept_role.assigned_by_user.full_name if dept_role.assigned_by_user else None,
            days_until_expiry=dept_role.days_until_expiry
        )
    
    def _recalculate_hierarchy(self, department: Department):
        """Recalculate hierarchy level and path for department"""
        if department.parent_department_id:
            parent = self.db.query(Department).filter(Department.id == department.parent_department_id).first()
            if parent:
                department.hierarchy_level = parent.hierarchy_level + 1
                if parent.hierarchy_path:
                    department.hierarchy_path = f"{parent.hierarchy_path}.{parent.id}"
                else:
                    department.hierarchy_path = str(parent.id)
            else:
                department.hierarchy_level = 0
                department.hierarchy_path = ""
        else:
            department.hierarchy_level = 0
            department.hierarchy_path = ""
        
        department.updated_at = datetime.utcnow()
    
    def _would_create_cycle(self, department_id: int, new_parent_id: int) -> bool:
        """Check if moving department would create circular reference"""
        if department_id == new_parent_id:
            return True
        
        # Check if new_parent is a descendant of department
        new_parent = self.db.query(Department).filter(Department.id == new_parent_id).first()
        if not new_parent or not new_parent.hierarchy_path:
            return False
        
        # Check if department_id is in new_parent's hierarchy path
        return str(department_id) in new_parent.hierarchy_path.split('.')
    
    def get_department_role_assignments(self, department_id: int) -> List[DepartmentRoleResponse]:
        """Get all role assignments for a department"""
        if not self.current_user.has_permission("organization.view", "core"):
            raise AuthorizationException("Insufficient permissions to view role assignments")
        
        dept_roles = self.db.query(DepartmentRole).filter(
            DepartmentRole.department_id == department_id,
            DepartmentRole.is_active == True
        ).options(
            joinedload(DepartmentRole.department),
            joinedload(DepartmentRole.role),
            joinedload(DepartmentRole.user),
            joinedload(DepartmentRole.assigned_by_user)
        ).all()
        
        return [self._convert_to_department_role_response(dr) for dr in dept_roles]