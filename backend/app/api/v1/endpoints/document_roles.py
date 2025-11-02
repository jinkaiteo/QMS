"""
Document Roles API Endpoints
Handles role-based access control for documents
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.document_roles_service import DocumentRolesService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Pydantic models for request/response

class RoleAssignmentRequest(BaseModel):
    user_id: int
    document_id: Optional[int] = None  # None for global roles
    role: str = Field(..., pattern="^(viewer|author|reviewer|approver|admin)$")
    effective_until: Optional[datetime] = None
    notes: str = ""

class RoleAssignmentResponse(BaseModel):
    role_id: int
    user_id: int
    document_id: Optional[int]
    role: str
    scope: str

class UserRoleResponse(BaseModel):
    id: int
    role: str
    document_id: Optional[int]
    document_number: Optional[str]
    document_title: Optional[str]
    effective_from: datetime
    effective_until: Optional[datetime]
    notes: str
    created_at: datetime
    assigned_by: str
    scope: str

class DocumentUserRoleResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    full_name: str
    role: str
    effective_from: datetime
    effective_until: Optional[datetime]
    notes: str
    created_at: datetime
    assigned_by: str
    scope: str

class BulkAssignmentRequest(BaseModel):
    assignments: List[RoleAssignmentRequest]

class RoleStatsResponse(BaseModel):
    role_breakdown: dict
    overall: dict
    role_hierarchy: List[str]

class ExpiringRoleResponse(BaseModel):
    role_id: int
    user_id: int
    username: str
    email: str
    document_id: Optional[int]
    document_number: Optional[str]
    document_title: Optional[str]
    role: str
    effective_until: datetime
    days_until_expiry: int
    scope: str

# Role assignment endpoints

@router.post("/assign", response_model=RoleAssignmentResponse)
async def assign_document_role(
    request: RoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a role to a user for a document or globally"""
    try:
        service = DocumentRolesService(db)
        
        result = service.assign_document_role(
            user_id=request.user_id,
            document_id=request.document_id,
            role=request.role,
            assigned_by_id=current_user.id,
            effective_until=request.effective_until,
            notes=request.notes
        )
        
        return RoleAssignmentResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign role: {str(e)}")

@router.delete("/roles/{role_id}")
async def remove_document_role(
    role_id: int,
    reason: str = Query("Role removal", description="Reason for removing the role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a document role assignment"""
    try:
        service = DocumentRolesService(db)
        
        success = service.remove_document_role(
            role_id=role_id,
            removed_by_id=current_user.id,
            reason=reason
        )
        
        if success:
            return {"message": "Role removed successfully", "role_id": role_id}
        else:
            raise HTTPException(status_code=404, detail="Role not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove role: {str(e)}")

@router.post("/bulk-assign")
async def bulk_assign_roles(
    request: BulkAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk assign multiple roles"""
    try:
        service = DocumentRolesService(db)
        
        # Convert Pydantic models to dicts
        assignments = [assignment.dict() for assignment in request.assignments]
        
        results = service.bulk_assign_roles(
            assignments=assignments,
            assigned_by_id=current_user.id
        )
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        return {
            "message": f"Bulk assignment completed: {len(successful)} successful, {len(failed)} failed",
            "successful_assignments": len(successful),
            "failed_assignments": len(failed),
            "failures": failed
        }
        
    except Exception as e:
        logger.error(f"Error in bulk role assignment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk assign roles: {str(e)}")

# Query endpoints

@router.get("/user/{user_id}/roles", response_model=List[UserRoleResponse])
async def get_user_roles(
    user_id: int,
    document_id: Optional[int] = Query(None, description="Filter by specific document ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get roles for a specific user"""
    try:
        # Basic authorization - users can see their own roles, admins can see all
        if user_id != current_user.id and not hasattr(current_user, 'is_admin'):
            raise HTTPException(status_code=403, detail="Not authorized to view other user's roles")
        
        service = DocumentRolesService(db)
        roles = service.get_user_document_roles(user_id, document_id)
        
        return [UserRoleResponse(**role) for role in roles]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting roles for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user roles: {str(e)}")

@router.get("/my-roles", response_model=List[UserRoleResponse])
async def get_my_roles(
    document_id: Optional[int] = Query(None, description="Filter by specific document ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get roles for the current user"""
    try:
        service = DocumentRolesService(db)
        roles = service.get_user_document_roles(current_user.id, document_id)
        
        return [UserRoleResponse(**role) for role in roles]
        
    except Exception as e:
        logger.error(f"Error getting roles for current user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user roles: {str(e)}")

@router.get("/document/{document_id}/users", response_model=List[DocumentUserRoleResponse])
async def get_document_user_roles(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all user roles for a specific document"""
    try:
        service = DocumentRolesService(db)
        roles = service.get_document_user_roles(document_id)
        
        return [DocumentUserRoleResponse(**role) for role in roles]
        
    except Exception as e:
        logger.error(f"Error getting user roles for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document user roles: {str(e)}")

@router.get("/document/{document_id}/users-with-permission")
async def get_users_with_permission(
    document_id: int,
    permission: str = Query(..., description="Required permission level"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get users who have a specific permission for a document"""
    try:
        service = DocumentRolesService(db)
        users = service.get_users_with_permission(document_id, permission)
        
        return {
            "document_id": document_id,
            "required_permission": permission,
            "users_with_permission": users,
            "total_users": len(users)
        }
        
    except Exception as e:
        logger.error(f"Error getting users with permission {permission} for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get users with permission: {str(e)}")

# Permission checking endpoints

@router.get("/user/{user_id}/permission/{document_id}")
async def check_user_permission(
    user_id: int,
    document_id: int,
    permission: str = Query(..., description="Permission to check"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if a user has a specific permission for a document"""
    try:
        service = DocumentRolesService(db)
        
        has_permission = service.check_user_permission(user_id, document_id, permission)
        user_role = service.get_user_highest_role(user_id, document_id)
        
        return {
            "user_id": user_id,
            "document_id": document_id,
            "required_permission": permission,
            "has_permission": has_permission,
            "user_highest_role": user_role
        }
        
    except Exception as e:
        logger.error(f"Error checking permission for user {user_id} on document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check permission: {str(e)}")

@router.get("/my-permission/{document_id}")
async def check_my_permission(
    document_id: int,
    permission: str = Query(..., description="Permission to check"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if the current user has a specific permission for a document"""
    try:
        service = DocumentRolesService(db)
        
        has_permission = service.check_user_permission(current_user.id, document_id, permission)
        user_role = service.get_user_highest_role(current_user.id, document_id)
        
        return {
            "user_id": current_user.id,
            "document_id": document_id,
            "required_permission": permission,
            "has_permission": has_permission,
            "user_highest_role": user_role
        }
        
    except Exception as e:
        logger.error(f"Error checking permission for current user on document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check permission: {str(e)}")

# Statistics and monitoring endpoints

@router.get("/stats", response_model=RoleStatsResponse)
async def get_role_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get role assignment statistics"""
    try:
        service = DocumentRolesService(db)
        stats = service.get_role_statistics()
        
        return RoleStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting role statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get role statistics: {str(e)}")

@router.get("/expiring", response_model=List[ExpiringRoleResponse])
async def get_expiring_roles(
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get roles that will expire within the specified number of days"""
    try:
        service = DocumentRolesService(db)
        expiring_roles = service.get_expiring_roles(days_ahead)
        
        return [ExpiringRoleResponse(**role) for role in expiring_roles]
        
    except Exception as e:
        logger.error(f"Error getting expiring roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get expiring roles: {str(e)}")

# Utility endpoints

@router.get("/hierarchy")
async def get_role_hierarchy():
    """Get the role hierarchy and permission levels"""
    return {
        "role_hierarchy": DocumentRolesService.ROLE_HIERARCHY,
        "descriptions": {
            "viewer": "Can view documents and basic information",
            "author": "Can create and edit documents, view permissions",
            "reviewer": "Can review documents, all author permissions",
            "approver": "Can approve documents, all reviewer permissions", 
            "admin": "Full access to all document operations and role management"
        },
        "permissions": {
            "view": "viewer",
            "edit": "author",
            "review": "reviewer", 
            "approve": "approver",
            "admin": "admin"
        }
    }

@router.post("/initialize-default-roles")
async def initialize_default_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize default roles for the current user (admin only)"""
    try:
        # Check if user has admin privileges (basic check)
        if not hasattr(current_user, 'is_admin') and current_user.username != 'admin':
            raise HTTPException(status_code=403, detail="Only admin users can initialize default roles")
        
        service = DocumentRolesService(db)
        
        # Assign global admin role to current user if not already assigned
        try:
            result = service.assign_document_role(
                user_id=current_user.id,
                document_id=None,  # Global role
                role='admin',
                assigned_by_id=current_user.id,
                notes='Default admin role initialization'
            )
            
            return {
                "message": "Default admin role initialized successfully",
                "role_assignment": result
            }
            
        except ValueError as e:
            if "already has" in str(e):
                return {"message": "Default roles already initialized"}
            else:
                raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing default roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize default roles: {str(e)}")

# Health check endpoint
@router.get("/health")
async def roles_health_check():
    """Health check for document roles service"""
    return {
        "status": "healthy",
        "service": "document_roles",
        "timestamp": datetime.now(),
        "role_hierarchy": DocumentRolesService.ROLE_HIERARCHY,
        "endpoints_available": [
            "assign", "bulk-assign", "user-roles", "document-users", 
            "permission-check", "stats", "expiring", "hierarchy"
        ]
    }