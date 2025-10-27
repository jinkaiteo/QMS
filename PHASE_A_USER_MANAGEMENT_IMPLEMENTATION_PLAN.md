# 🚀 Phase A: User Management & RBAC Enhancement - Implementation Plan

## 📊 **Project Overview**

**Phase**: A - User Management & RBAC Enhancement  
**Duration**: 2-3 weeks (15 working days)  
**Priority**: HIGH  
**Start Date**: Ready to begin immediately  
**Team**: Building on current QMS Platform foundation  

### **🎯 Phase Objectives:**
- Enhance user management with advanced role assignment capabilities
- Implement department and organization hierarchies
- Add comprehensive user profile management
- Create intuitive user onboarding workflows
- Build user activity monitoring and reporting

---

## 🏗️ **Technical Architecture Plan**

### **Current Foundation (What We Have):**
```
✅ Enterprise Authentication System
✅ JWT Token Management with Security
✅ Basic User Model with Roles
✅ Permission System Infrastructure
✅ Database Schema with Users/Roles Tables
✅ Security Middleware and Audit Logging
```

### **Phase A Additions (What We'll Build):**
```
🔜 Enhanced User Profile Management
🔜 Department/Organization Hierarchies  
🔜 Advanced Role Assignment Interface
🔜 User Activity Tracking System
🔜 Password Policy Management
🔜 User Onboarding Workflows
```

---

## 📅 **Detailed Sprint Planning**

### **Sprint 1: User Profile Enhancement (Days 1-5)**

#### **Day 1-2: Database Schema Extensions**
```sql
-- Enhanced User Profile Table Extensions
ALTER TABLE users ADD COLUMN profile_picture_url VARCHAR(255);
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);
ALTER TABLE users ADD COLUMN job_title VARCHAR(100);
ALTER TABLE users ADD COLUMN hire_date DATE;
ALTER TABLE users ADD COLUMN employee_id VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN supervisor_id INTEGER REFERENCES users(id);
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0;

-- User Preferences Table
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

-- User Sessions Table for Activity Tracking
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### **Day 3-4: Enhanced User Model Development**
```python
# backend/app/models/user_profile.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserProfile(BaseModel):
    __tablename__ = "user_profiles"
    
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    profile_picture_url = Column(String(255))
    phone_number = Column(String(20))
    job_title = Column(String(100))
    hire_date = Column(Date)
    employee_id = Column(String(50), unique=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    bio = Column(Text)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="profile")
    supervisor = relationship("User", foreign_keys=[supervisor_id])

class UserPreference(BaseModel):
    __tablename__ = "user_preferences"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="preferences")

class UserSession(BaseModel):
    __tablename__ = "user_sessions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    started_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    ended_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
```

#### **Day 5: User Profile API Endpoints**
```python
# backend/app/api/v1/endpoints/user_profiles.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from app.schemas.user_profile import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from app.services.user_profile_service import UserProfileService

router = APIRouter()

@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    service = UserProfileService(db, current_user)
    return service.get_user_profile(current_user.id)

@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    service = UserProfileService(db, current_user)
    return service.update_profile(current_user.id, profile_data)

@router.post("/me/profile/avatar")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture"""
    service = UserProfileService(db, current_user)
    return service.upload_profile_picture(current_user.id, file)
```

---

### **Sprint 2: Department & Organization Hierarchies (Days 6-10)**

#### **Day 6-7: Organizational Structure Database Design**
```sql
-- Enhanced Departments Table
ALTER TABLE departments ADD COLUMN parent_department_id INTEGER REFERENCES departments(id);
ALTER TABLE departments ADD COLUMN department_code VARCHAR(20) UNIQUE;
ALTER TABLE departments ADD COLUMN department_head_id INTEGER REFERENCES users(id);
ALTER TABLE departments ADD COLUMN cost_center VARCHAR(50);
ALTER TABLE departments ADD COLUMN location VARCHAR(100);

-- Organizations Table (Multi-tenant support)
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    organization_code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    logo_url VARCHAR(255),
    website VARCHAR(255),
    primary_contact_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Department Roles Bridge Table
CREATE TABLE department_roles (
    id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(department_id, role_id, user_id)
);
```

#### **Day 8-9: Organizational Hierarchy Service**
```python
# backend/app/services/organization_service.py
class OrganizationService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def get_department_hierarchy(self, department_id: int = None):
        """Get department hierarchy tree"""
        # Implementation for recursive department tree
        pass
    
    def assign_department_role(self, user_id: int, department_id: int, role_id: int):
        """Assign role to user in specific department"""
        # Verify permissions
        if not self.current_user.has_permission("user.manage_roles", "core"):
            raise AuthorizationException("Insufficient permissions")
        
        # Create department role assignment
        dept_role = DepartmentRole(
            department_id=department_id,
            role_id=role_id,
            user_id=user_id,
            assigned_by=self.current_user.id
        )
        self.db.add(dept_role)
        self.db.commit()
        
        # Log the assignment
        audit_logger.log_user_management_event(
            admin_user_id=self.current_user.id,
            target_user_id=user_id,
            event_type="role_assigned",
            details={"department_id": department_id, "role_id": role_id}
        )
    
    def get_user_effective_permissions(self, user_id: int, department_id: int = None):
        """Calculate user's effective permissions considering hierarchy"""
        # Implementation for permission inheritance
        pass
```

#### **Day 10: Organization Management API**
```python
# backend/app/api/v1/endpoints/organizations.py
@router.get("/departments/hierarchy")
async def get_department_hierarchy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organizational department hierarchy"""
    service = OrganizationService(db, current_user)
    return service.get_department_hierarchy()

@router.post("/departments/{department_id}/roles/{role_id}/assign/{user_id}")
async def assign_department_role(
    department_id: int,
    role_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign role to user in specific department"""
    service = OrganizationService(db, current_user)
    return service.assign_department_role(user_id, department_id, role_id)
```

---

### **Sprint 3: Advanced Role Management Interface (Days 11-15)**

#### **Day 11-12: Role Management Service Enhancement**
```python
# backend/app/services/role_management_service.py
class RoleManagementService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def get_role_assignment_matrix(self, department_id: int = None):
        """Get comprehensive role assignment matrix"""
        query = self.db.query(User, Role, Department).join(UserRole).join(Role)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        # Build matrix structure
        matrix = {}
        for user, role, dept in query:
            if user.id not in matrix:
                matrix[user.id] = {
                    "user": user,
                    "roles": [],
                    "departments": []
                }
            matrix[user.id]["roles"].append(role)
            matrix[user.id]["departments"].append(dept)
        
        return list(matrix.values())
    
    def bulk_role_assignment(self, assignments: List[RoleAssignmentRequest]):
        """Perform bulk role assignments with validation"""
        for assignment in assignments:
            # Validate permissions
            self._validate_role_assignment_permission(assignment)
            
            # Create or update role assignment
            self._assign_role(assignment.user_id, assignment.role_id, assignment.department_id)
        
        self.db.commit()
        
        # Log bulk assignment
        audit_logger.log_user_management_event(
            admin_user_id=self.current_user.id,
            event_type="bulk_role_assignment",
            details={"assignments_count": len(assignments)}
        )
    
    def get_role_suggestions(self, user_id: int):
        """Get AI-powered role suggestions based on user profile"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Simple rule-based suggestions (can be enhanced with ML)
        suggestions = []
        
        if user.job_title and "manager" in user.job_title.lower():
            suggestions.extend(["Department Manager", "Quality Coordinator"])
        
        if user.department_id:
            dept_common_roles = self._get_common_department_roles(user.department_id)
            suggestions.extend(dept_common_roles)
        
        return suggestions
```

#### **Day 13: User Activity Tracking System**
```python
# backend/app/services/user_activity_service.py
class UserActivityService:
    def __init__(self, db: Session):
        self.db = db
    
    def track_user_login(self, user: User, request: Request):
        """Track user login activity"""
        session = UserSession(
            user_id=user.id,
            session_token=secrets.token_urlsafe(32),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            started_at=datetime.utcnow()
        )
        self.db.add(session)
        
        # Update user last login
        user.last_login_at = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        
        self.db.commit()
        return session
    
    def get_user_activity_report(self, user_id: int, days: int = 30):
        """Generate user activity report"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.started_at >= cutoff_date
        ).all()
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_sessions": len(sessions),
            "total_time": self._calculate_total_session_time(sessions),
            "login_frequency": len(sessions) / days,
            "most_active_hours": self._get_most_active_hours(sessions),
            "device_breakdown": self._get_device_breakdown(sessions)
        }
    
    def get_department_activity_dashboard(self, department_id: int):
        """Get department-wide activity dashboard"""
        # Implementation for department activity analytics
        pass
```

#### **Day 14-15: User Management Frontend Components**
```typescript
// frontend/src/components/UserManagement/UserRoleMatrix.tsx
interface UserRoleMatrixProps {
  departmentId?: number;
  onRoleAssignmentChange: (assignments: RoleAssignment[]) => void;
}

export const UserRoleMatrix: React.FC<UserRoleMatrixProps> = ({
  departmentId,
  onRoleAssignmentChange
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [assignments, setAssignments] = useState<RoleAssignment[]>([]);
  
  // Drag and drop functionality for role assignments
  const handleRoleDrop = (userId: number, roleId: number) => {
    const newAssignment: RoleAssignment = {
      userId,
      roleId,
      departmentId: departmentId || null,
      assignedAt: new Date().toISOString()
    };
    
    setAssignments(prev => [...prev, newAssignment]);
    onRoleAssignmentChange([...assignments, newAssignment]);
  };
  
  return (
    <div className="user-role-matrix">
      <div className="matrix-header">
        <div className="user-column">Users</div>
        {roles.map(role => (
          <div key={role.id} className="role-column">
            {role.name}
          </div>
        ))}
      </div>
      
      {users.map(user => (
        <UserRoleRow
          key={user.id}
          user={user}
          roles={roles}
          assignments={assignments.filter(a => a.userId === user.id)}
          onRoleDrop={handleRoleDrop}
        />
      ))}
    </div>
  );
};

// frontend/src/components/UserManagement/UserActivityDashboard.tsx
export const UserActivityDashboard: React.FC = () => {
  const [activityData, setActivityData] = useState<ActivityData[]>([]);
  
  return (
    <div className="user-activity-dashboard">
      <div className="dashboard-header">
        <h2>User Activity Dashboard</h2>
        <DateRangePicker onChange={handleDateRangeChange} />
      </div>
      
      <div className="activity-metrics">
        <MetricCard title="Active Users" value={activityData.length} />
        <MetricCard title="Total Sessions" value={getTotalSessions()} />
        <MetricCard title="Avg Session Time" value={getAvgSessionTime()} />
      </div>
      
      <div className="activity-charts">
        <LineChart data={activityData} />
        <BarChart data={getDepartmentActivity()} />
      </div>
    </div>
  );
};
```

---

## 📊 **Implementation Checklist**

### **Backend Development:**
- [ ] Database schema extensions for user profiles
- [ ] Enhanced User model with profile relationships
- [ ] Department hierarchy implementation
- [ ] Role management service with bulk operations
- [ ] User activity tracking system
- [ ] Password policy management
- [ ] API endpoints for all new functionality
- [ ] Permission validations for user management operations

### **Frontend Development:**
- [ ] User profile management interface
- [ ] Role assignment matrix with drag-and-drop
- [ ] Department hierarchy tree view
- [ ] User activity dashboard with charts
- [ ] Password policy configuration UI
- [ ] User onboarding wizard
- [ ] Responsive design for all components

### **Testing & Quality:**
- [ ] Unit tests for all services
- [ ] Integration tests for role assignment workflows
- [ ] Frontend component tests
- [ ] Security testing for permission escalation
- [ ] Performance testing for bulk operations
- [ ] User acceptance testing

### **Documentation:**
- [ ] API documentation updates
- [ ] User manual for role management
- [ ] Administrator guide for user onboarding
- [ ] Technical documentation for developers

---

## 🎯 **Success Metrics & Acceptance Criteria**

### **Functional Requirements:**
- [ ] Users can update their profiles with pictures and contact info
- [ ] Administrators can assign roles across department hierarchies
- [ ] Bulk role assignments work for 100+ users simultaneously
- [ ] User activity tracking captures all login sessions
- [ ] Password policies are configurable and enforced
- [ ] Department hierarchy supports unlimited nesting levels

### **Performance Requirements:**
- [ ] Role assignment operations complete within 2 seconds
- [ ] User activity dashboard loads within 3 seconds
- [ ] Bulk operations handle 500+ users without timeout
- [ ] Database queries optimized with proper indexing

### **Security Requirements:**
- [ ] All user management operations require appropriate permissions
- [ ] Profile picture uploads are validated and secured
- [ ] User activity data is properly encrypted
- [ ] Audit logs capture all administrative actions

### **Usability Requirements:**
- [ ] User profile interface is intuitive and easy to navigate
- [ ] Role assignment matrix is visually clear and functional
- [ ] User onboarding wizard reduces setup time by 75%
- [ ] Activity dashboard provides actionable insights

---

## 🚀 **Ready to Begin Implementation**

**Phase A is perfectly positioned to leverage your excellent authentication foundation while delivering immediate business value through enhanced user management capabilities.**

**Next Steps:**
1. **Confirm Implementation Plan** - Review and approve this detailed plan
2. **Setup Development Environment** - Prepare database migrations and development branch
3. **Begin Sprint 1** - Start with user profile enhancements
4. **Iterative Development** - Build, test, and validate each component

**Would you like to begin with Sprint 1 (User Profile Enhancement) or would you prefer to adjust any aspects of this implementation plan?**

This comprehensive plan will transform your QMS Platform into a user-friendly, enterprise-ready system with powerful user management capabilities! 🎉