# 🏗️ Phase A Sprint 2: Department & Organization Hierarchies

## 📊 **Sprint Overview**

**Sprint**: 2 - Department & Organization Hierarchies  
**Phase**: A - User Management & RBAC Enhancement  
**Duration**: Days 6-10 (5 working days)  
**Status**: 🚀 **STARTING NOW**  
**Foundation**: Building on Sprint 1's user profile system  

### **🎯 Sprint Objectives:**
- Implement hierarchical department structure with unlimited nesting
- Create organization management for multi-tenant support
- Build department-specific role assignments
- Add organizational hierarchy visualization
- Enable department-based permission inheritance

---

## 🏗️ **Technical Architecture Plan**

### **Sprint 1 Foundation (What We Have):**
```
✅ Enhanced User Profiles with supervisor relationships
✅ User Activity Tracking and Analytics
✅ Permission-based Access Control
✅ Comprehensive Profile Management
✅ User Preferences and Settings
```

### **Sprint 2 Additions (What We'll Build):**
```
🔜 Hierarchical Department Structure (unlimited nesting)
🔜 Organization Management (multi-tenant support)
🔜 Department-specific Role Assignments
🔜 Organizational Hierarchy APIs
🔜 Department Permission Inheritance
🔜 Organizational Analytics and Reporting
```

---

## 📅 **Sprint 2 Daily Plan**

### **Day 6: Database Schema & Models**

#### **Morning: Enhanced Department Schema**
```sql
-- Enhanced Departments Table with Hierarchy
ALTER TABLE departments ADD COLUMN parent_department_id INTEGER REFERENCES departments(id);
ALTER TABLE departments ADD COLUMN department_code VARCHAR(20) UNIQUE;
ALTER TABLE departments ADD COLUMN department_head_id INTEGER REFERENCES users(id);
ALTER TABLE departments ADD COLUMN cost_center VARCHAR(50);
ALTER TABLE departments ADD COLUMN location VARCHAR(100);
ALTER TABLE departments ADD COLUMN department_type VARCHAR(50); -- 'operational', 'administrative', 'quality'
ALTER TABLE departments ADD COLUMN hierarchy_path TEXT; -- Materialized path for efficient queries
ALTER TABLE departments ADD COLUMN hierarchy_level INTEGER DEFAULT 0;

-- Organizations Enhancement (already exists, enhance)
ALTER TABLE organizations ADD COLUMN organization_type VARCHAR(50); -- 'manufacturing', 'laboratory', 'corporate'
ALTER TABLE organizations ADD COLUMN parent_organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE organizations ADD COLUMN regulatory_region VARCHAR(50); -- 'FDA', 'EMA', 'PMDA'

-- Department Roles Bridge Table
CREATE TABLE department_roles (
    id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(department_id, role_id, user_id)
);
```

#### **Afternoon: SQLAlchemy Models**
```python
# backend/app/models/organization_management/department_hierarchy.py
class Department(BaseModel):
    __tablename__ = "departments"
    
    # Enhanced fields
    parent_department_id = Column(Integer, ForeignKey("departments.id"))
    department_code = Column(String(20), unique=True)
    department_head_id = Column(Integer, ForeignKey("users.id"))
    cost_center = Column(String(50))
    location = Column(String(100))
    department_type = Column(String(50))
    hierarchy_path = Column(Text)  # e.g., "1.2.5" for efficient queries
    hierarchy_level = Column(Integer, default=0)
    
    # Relationships
    parent_department = relationship("Department", remote_side="Department.id")
    child_departments = relationship("Department", back_populates="parent_department")
    department_head = relationship("User", foreign_keys=[department_head_id])
    department_roles = relationship("DepartmentRole", back_populates="department")
    
    @property
    def full_hierarchy_name(self):
        """Get full hierarchical name like 'Corporate > Manufacturing > Quality'"""
        if self.parent_department:
            return f"{self.parent_department.full_hierarchy_name} > {self.name}"
        return self.name
    
    def get_all_descendants(self):
        """Get all descendant departments recursively"""
        descendants = []
        for child in self.child_departments:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

class DepartmentRole(BaseModel):
    __tablename__ = "department_roles"
    
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    department = relationship("Department", back_populates="department_roles")
    role = relationship("Role")
    user = relationship("User", foreign_keys=[user_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
```

---

### **Day 7: Organization Service Layer**

#### **Core Organization Service**
```python
# backend/app/services/organization_management/organization_service.py
class OrganizationService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def get_department_hierarchy_tree(self, organization_id: int = None, department_id: int = None):
        """Get complete department hierarchy as nested tree structure"""
        if not self.current_user.has_permission("organization.view", "core"):
            raise AuthorizationException("Insufficient permissions")
        
        # Get root departments (no parent)
        query = self.db.query(Department).filter(Department.parent_department_id.is_(None))
        
        if organization_id:
            query = query.filter(Department.organization_id == organization_id)
        elif department_id:
            # Get specific department and its children
            query = self.db.query(Department).filter(Department.id == department_id)
        
        root_departments = query.all()
        
        def build_tree(dept):
            return {
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
                "department_type": dept.department_type,
                "location": dept.location,
                "cost_center": dept.cost_center,
                "hierarchy_level": dept.hierarchy_level,
                "hierarchy_path": dept.hierarchy_path,
                "department_head": {
                    "id": dept.department_head.id,
                    "full_name": dept.department_head.full_name,
                    "job_title": dept.department_head.job_title
                } if dept.department_head else None,
                "user_count": len(dept.users),
                "children": [build_tree(child) for child in dept.child_departments]
            }
        
        return [build_tree(dept) for dept in root_departments]
    
    def assign_department_role(self, user_id: int, department_id: int, role_id: int, 
                             valid_from: datetime = None, valid_until: datetime = None):
        """Assign role to user in specific department"""
        if not self.current_user.has_permission("user.manage_roles", "core"):
            raise AuthorizationException("Insufficient permissions")
        
        # Validate department exists and user has access
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Check if assignment already exists
        existing = self.db.query(DepartmentRole).filter(
            DepartmentRole.user_id == user_id,
            DepartmentRole.department_id == department_id,
            DepartmentRole.role_id == role_id,
            DepartmentRole.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Role already assigned to user in this department")
        
        # Create new assignment
        dept_role = DepartmentRole(
            user_id=user_id,
            department_id=department_id,
            role_id=role_id,
            assigned_by=self.current_user.id,
            valid_from=valid_from or datetime.utcnow(),
            valid_until=valid_until
        )
        
        self.db.add(dept_role)
        self.db.commit()
        
        # Update department hierarchy path if needed
        self._update_hierarchy_paths(department_id)
        
        # Log the assignment
        audit_logger.log_user_management_event(
            admin_user_id=self.current_user.id,
            target_user_id=user_id,
            event_type="department_role_assigned",
            details={
                "department_id": department_id,
                "role_id": role_id,
                "valid_from": valid_from.isoformat() if valid_from else None,
                "valid_until": valid_until.isoformat() if valid_until else None
            }
        )
        
        return dept_role
    
    def get_user_effective_permissions(self, user_id: int, department_id: int = None):
        """Calculate user's effective permissions considering department hierarchy"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        permissions = set()
        
        # Get global role permissions
        for user_role in user.user_roles:
            if user_role.is_active and user_role.role.is_active:
                permissions.update(user_role.role.permissions or [])
        
        # Get department-specific permissions
        dept_roles = self.db.query(DepartmentRole).filter(
            DepartmentRole.user_id == user_id,
            DepartmentRole.is_active == True
        ).all()
        
        for dept_role in dept_roles:
            # Include permissions if no specific department requested 
            # or if the role is in the requested department or its parents
            if not department_id or self._is_department_in_hierarchy(dept_role.department_id, department_id):
                permissions.update(dept_role.role.permissions or [])
        
        return list(permissions)
    
    def create_department(self, organization_id: int, dept_data: DepartmentCreateRequest):
        """Create new department with hierarchy support"""
        if not self.current_user.has_permission("organization.manage", "core"):
            raise AuthorizationException("Insufficient permissions")
        
        # Calculate hierarchy level and path
        hierarchy_level = 0
        hierarchy_path = ""
        
        if dept_data.parent_department_id:
            parent_dept = self.db.query(Department).filter(
                Department.id == dept_data.parent_department_id
            ).first()
            
            if not parent_dept:
                raise HTTPException(status_code=404, detail="Parent department not found")
            
            hierarchy_level = parent_dept.hierarchy_level + 1
            hierarchy_path = f"{parent_dept.hierarchy_path}.{parent_dept.id}" if parent_dept.hierarchy_path else str(parent_dept.id)
        
        # Create department
        department = Department(
            organization_id=organization_id,
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
                "organization_id": organization_id,
                "parent_department_id": dept_data.parent_department_id
            }
        )
        
        return department
    
    def _update_hierarchy_paths(self, department_id: int):
        """Update hierarchy paths for department and all descendants"""
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return
        
        # Update this department's path
        if department.parent_department_id:
            parent = self.db.query(Department).filter(Department.id == department.parent_department_id).first()
            if parent:
                department.hierarchy_path = f"{parent.hierarchy_path}.{parent.id}" if parent.hierarchy_path else str(parent.id)
                department.hierarchy_level = parent.hierarchy_level + 1
        else:
            department.hierarchy_path = ""
            department.hierarchy_level = 0
        
        # Recursively update children
        for child in department.child_departments:
            self._update_hierarchy_paths(child.id)
        
        self.db.commit()
    
    def _is_department_in_hierarchy(self, role_dept_id: int, target_dept_id: int) -> bool:
        """Check if role department is in the hierarchy path of target department"""
        target_dept = self.db.query(Department).filter(Department.id == target_dept_id).first()
        if not target_dept:
            return False
        
        # Check if role_dept_id is in the hierarchy path
        if target_dept.hierarchy_path:
            hierarchy_ids = [int(x) for x in target_dept.hierarchy_path.split('.')]
            return role_dept_id in hierarchy_ids or role_dept_id == target_dept_id
        
        return role_dept_id == target_dept_id
```

---

### **Day 8: Advanced Hierarchy Features**

#### **Department Analytics Service**
```python
# backend/app/services/organization_management/department_analytics.py
class DepartmentAnalyticsService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def get_department_metrics(self, department_id: int, include_children: bool = True):
        """Get comprehensive department metrics"""
        if not self.current_user.has_permission("analytics.view", "core"):
            raise AuthorizationException("Insufficient permissions")
        
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Get user counts
        direct_users = len(department.users)
        
        if include_children:
            all_descendant_users = 0
            for desc_dept in department.get_all_descendants():
                all_descendant_users += len(desc_dept.users)
            total_users = direct_users + all_descendant_users
        else:
            total_users = direct_users
        
        # Get role distribution
        role_distribution = {}
        dept_roles = self.db.query(DepartmentRole).filter(
            DepartmentRole.department_id == department_id,
            DepartmentRole.is_active == True
        ).all()
        
        for dept_role in dept_roles:
            role_name = dept_role.role.display_name
            role_distribution[role_name] = role_distribution.get(role_name, 0) + 1
        
        # Get activity metrics (from Sprint 1)
        recent_logins = self.db.query(UserSession).join(User).filter(
            User.department_id == department_id,
            UserSession.started_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        return {
            "department_id": department_id,
            "department_name": department.name,
            "hierarchy_level": department.hierarchy_level,
            "direct_users": direct_users,
            "total_users": total_users,
            "child_departments": len(department.child_departments),
            "role_distribution": role_distribution,
            "recent_logins_30d": recent_logins,
            "department_head": {
                "id": department.department_head.id,
                "full_name": department.department_head.full_name
            } if department.department_head else None
        }
    
    def get_organization_hierarchy_analytics(self, organization_id: int):
        """Get organization-wide hierarchy analytics"""
        org = self.db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get all departments in organization
        departments = self.db.query(Department).filter(
            Department.organization_id == organization_id
        ).all()
        
        # Calculate hierarchy statistics
        max_depth = max([dept.hierarchy_level for dept in departments]) if departments else 0
        total_departments = len(departments)
        
        # Department type distribution
        type_distribution = {}
        for dept in departments:
            dept_type = dept.department_type or 'unspecified'
            type_distribution[dept_type] = type_distribution.get(dept_type, 0) + 1
        
        # User distribution by hierarchy level
        level_distribution = {}
        for dept in departments:
            level = dept.hierarchy_level
            user_count = len(dept.users)
            level_distribution[f"Level_{level}"] = level_distribution.get(f"Level_{level}", 0) + user_count
        
        return {
            "organization_id": organization_id,
            "organization_name": org.name,
            "total_departments": total_departments,
            "max_hierarchy_depth": max_depth,
            "department_type_distribution": type_distribution,
            "user_distribution_by_level": level_distribution,
            "total_users": sum(len(dept.users) for dept in departments)
        }
```

---

### **Day 9: API Endpoints & Integration**

#### **Department Hierarchy API**
```python
# backend/app/api/v1/endpoints/department_hierarchy.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

router = APIRouter()

@router.get("/organizations/{org_id}/departments/hierarchy")
async def get_department_hierarchy(
    org_id: int,
    department_id: Optional[int] = Query(None, description="Root department ID (optional)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get hierarchical department tree for organization
    
    Returns nested tree structure with:
    - Department information
    - Child departments recursively
    - User counts and department heads
    - Hierarchy paths and levels
    """
    service = OrganizationService(db, current_user)
    return service.get_department_hierarchy_tree(org_id, department_id)

@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept_data: DepartmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new department with optional parent department
    
    Automatically calculates:
    - Hierarchy level based on parent
    - Hierarchy path for efficient queries
    - Department code validation
    """
    service = OrganizationService(db, current_user)
    return service.create_department(dept_data.organization_id, dept_data)

@router.post("/departments/{dept_id}/roles/{role_id}/assign/{user_id}")
async def assign_department_role(
    dept_id: int,
    role_id: int,
    user_id: int,
    assignment_data: DepartmentRoleAssignmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign role to user in specific department
    
    Features:
    - Time-bound role assignments
    - Department-specific permissions
    - Automatic hierarchy inheritance
    """
    service = OrganizationService(db, current_user)
    return service.assign_department_role(
        user_id, dept_id, role_id, 
        assignment_data.valid_from, 
        assignment_data.valid_until
    )

@router.get("/departments/{dept_id}/analytics")
async def get_department_analytics(
    dept_id: int,
    include_children: bool = Query(True, description="Include child department metrics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive department analytics
    
    Includes:
    - User counts (direct and hierarchical)
    - Role distribution
    - Activity metrics
    - Child department statistics
    """
    service = DepartmentAnalyticsService(db, current_user)
    return service.get_department_metrics(dept_id, include_children)

@router.get("/users/{user_id}/effective-permissions")
async def get_user_effective_permissions(
    user_id: int,
    department_id: Optional[int] = Query(None, description="Context department ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's effective permissions considering department hierarchy
    
    Combines:
    - Global role permissions
    - Department-specific role permissions
    - Inherited permissions from parent departments
    """
    service = OrganizationService(db, current_user)
    return service.get_user_effective_permissions(user_id, department_id)
```

---

### **Day 10: Frontend Integration & Testing**

#### **Department Hierarchy Component**
```typescript
// frontend/src/components/Organization/DepartmentHierarchy.tsx
interface DepartmentNode {
  id: number;
  name: string;
  code: string;
  department_type: string;
  location: string;
  hierarchy_level: number;
  department_head?: {
    id: number;
    full_name: string;
    job_title: string;
  };
  user_count: number;
  children: DepartmentNode[];
}

export const DepartmentHierarchy: React.FC = () => {
  const [hierarchy, setHierarchy] = useState<DepartmentNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<DepartmentNode | null>(null);
  const [loading, setLoading] = useState(true);

  const renderDepartmentNode = (node: DepartmentNode, level: number = 0) => (
    <TreeNode
      key={node.id}
      nodeId={node.id}
      label={
        <DepartmentNodeLabel
          department={node}
          onSelect={() => setSelectedNode(node)}
          onEdit={() => handleEditDepartment(node)}
          onAddChild={() => handleAddChild(node)}
        />
      }
      style={{ marginLeft: level * 20 }}
    >
      {node.children.map(child => renderDepartmentNode(child, level + 1))}
    </TreeNode>
  );

  return (
    <div className="department-hierarchy">
      <div className="hierarchy-header">
        <Typography variant="h5">Department Hierarchy</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleAddRootDepartment()}
        >
          Add Department
        </Button>
      </div>

      <div className="hierarchy-content">
        <div className="tree-view">
          <TreeView
            defaultCollapseIcon={<ExpandMoreIcon />}
            defaultExpandIcon={<ChevronRightIcon />}
          >
            {hierarchy.map(node => renderDepartmentNode(node))}
          </TreeView>
        </div>

        <div className="department-details">
          {selectedNode && (
            <DepartmentDetails
              department={selectedNode}
              onUpdate={handleDepartmentUpdate}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// Department Role Assignment Matrix
export const DepartmentRoleMatrix: React.FC = () => {
  const [departments, setDepartments] = useState<DepartmentNode[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [assignments, setAssignments] = useState<DepartmentRoleAssignment[]>([]);

  return (
    <div className="department-role-matrix">
      <div className="matrix-controls">
        <DepartmentSelector 
          departments={departments}
          onSelect={handleDepartmentFilter}
        />
        <RoleFilter 
          roles={roles}
          onFilter={handleRoleFilter}
        />
      </div>

      <div className="assignment-matrix">
        <DataGrid
          rows={users}
          columns={[
            { field: 'full_name', headerName: 'User', width: 200 },
            { field: 'job_title', headerName: 'Title', width: 150 },
            ...roles.map(role => ({
              field: role.name,
              headerName: role.display_name,
              width: 120,
              renderCell: (params) => (
                <RoleAssignmentCell
                  user={params.row}
                  role={role}
                  assignments={assignments}
                  onAssign={handleRoleAssign}
                  onRevoke={handleRoleRevoke}
                />
              )
            }))
          ]}
          pageSize={20}
          checkboxSelection
          disableSelectionOnClick
        />
      </div>
    </div>
  );
};
```

---

## 🎯 **Sprint 2 Success Criteria**

### **Functional Requirements:**
- [ ] Create unlimited nested department hierarchies
- [ ] Assign users to departments at any level
- [ ] Assign roles to users within specific departments
- [ ] View department hierarchy as interactive tree
- [ ] Calculate effective permissions considering hierarchy
- [ ] Generate department analytics and metrics

### **Technical Requirements:**
- [ ] Efficient hierarchy queries using materialized paths
- [ ] Department-specific role assignments with time bounds
- [ ] Permission inheritance from parent departments
- [ ] Comprehensive audit logging for all changes
- [ ] Performance optimized for large hierarchies (1000+ departments)

### **Business Requirements:**
- [ ] Support pharmaceutical organizational structures
- [ ] Enable department-based access control
- [ ] Provide organizational analytics and insights
- [ ] Support regulatory compliance reporting
- [ ] Enable scalable user management

---

## 🚀 **Ready to Begin Sprint 2!**

**Sprint 2 builds perfectly on Sprint 1's foundation:**
- User profiles provide the base for organizational assignment
- Activity tracking supports department-level analytics
- Permission system extends to department-specific roles
- Supervisor relationships align with department hierarchy

**Next Steps:**
1. **Day 6**: Database schema and SQLAlchemy models
2. **Day 7**: Organization service layer with hierarchy logic
3. **Day 8**: Analytics service and advanced features
4. **Day 9**: API endpoints and integration
5. **Day 10**: Frontend components and testing

**Would you like to start with Day 6 database schema design, or would you prefer to adjust any aspects of this Sprint 2 plan?** 🚀