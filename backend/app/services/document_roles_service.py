"""
Document Roles Service
Handles role-based access control for documents according to QMS System Masterplan
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.logging import get_logger

logger = get_logger(__name__)

class DocumentRolesService:
    """Service for managing document roles and permissions"""
    
    # Role hierarchy (higher index = more permissions)
    ROLE_HIERARCHY = ['viewer', 'author', 'reviewer', 'approver', 'admin']
    
    def __init__(self, db: Session):
        self.db = db
    
    def assign_document_role(
        self,
        user_id: int,
        document_id: Optional[int],  # None for global roles
        role: str,
        assigned_by_id: int,
        effective_until: Optional[datetime] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Assign a role to a user for a document or globally"""
        try:
            # Validate role
            if role not in self.ROLE_HIERARCHY:
                raise ValueError(f"Invalid role: {role}. Must be one of: {self.ROLE_HIERARCHY}")
            
            # Check if assignment already exists
            existing_query = text("""
                SELECT id FROM document_roles 
                WHERE user_id = :user_id 
                  AND document_id = :document_id 
                  AND role = :role 
                  AND is_deleted = FALSE
            """)
            
            result = self.db.execute(existing_query, {
                'user_id': user_id,
                'document_id': document_id,
                'role': role
            })
            
            if result.fetchone():
                raise ValueError(f"User already has {role} role for this document")
            
            # Create role assignment
            insert_query = text("""
                INSERT INTO document_roles 
                (user_id, document_id, role, assigned_by_id, effective_until, notes, created_at, updated_at)
                VALUES (:user_id, :document_id, :role, :assigned_by_id, :effective_until, :notes, NOW(), NOW())
                RETURNING id
            """)
            
            result = self.db.execute(insert_query, {
                'user_id': user_id,
                'document_id': document_id,
                'role': role,
                'assigned_by_id': assigned_by_id,
                'effective_until': effective_until,
                'notes': notes
            })
            
            role_id = result.fetchone()[0]
            self.db.commit()
            
            scope = f"document {document_id}" if document_id else "global"
            logger.info(f"Role {role} assigned to user {user_id} for {scope} by user {assigned_by_id}")
            
            return {
                'role_id': role_id,
                'user_id': user_id,
                'document_id': document_id,
                'role': role,
                'scope': scope
            }
            
        except Exception as e:
            logger.error(f"Error assigning role {role} to user {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def remove_document_role(
        self,
        role_id: int,
        removed_by_id: int,
        reason: str = "Role removal"
    ) -> bool:
        """Remove a document role assignment"""
        try:
            # Soft delete the role
            query = text("""
                UPDATE document_roles 
                SET is_deleted = TRUE, updated_at = NOW()
                WHERE id = :role_id AND is_deleted = FALSE
            """)
            
            result = self.db.execute(query, {'role_id': role_id})
            
            if result.rowcount == 0:
                return False
            
            self.db.commit()
            
            logger.info(f"Role {role_id} removed by user {removed_by_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing role {role_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_user_document_roles(
        self,
        user_id: int,
        document_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get roles for a user, optionally for a specific document"""
        try:
            if document_id:
                # Get roles for specific document + global roles
                query = text("""
                    SELECT 
                        dr.id,
                        dr.role,
                        dr.document_id,
                        dr.effective_from,
                        dr.effective_until,
                        dr.notes,
                        dr.created_at,
                        d.document_number,
                        d.title,
                        u.username as assigned_by
                    FROM document_roles dr
                    LEFT JOIN documents d ON dr.document_id = d.id
                    JOIN users u ON dr.assigned_by_id = u.id
                    WHERE dr.user_id = :user_id 
                      AND (dr.document_id = :document_id OR dr.document_id IS NULL)
                      AND dr.is_deleted = FALSE
                      AND (dr.effective_until IS NULL OR dr.effective_until > NOW())
                    ORDER BY dr.document_id NULLS FIRST, dr.created_at DESC
                """)
                
                result = self.db.execute(query, {'user_id': user_id, 'document_id': document_id})
            else:
                # Get all roles for user
                query = text("""
                    SELECT 
                        dr.id,
                        dr.role,
                        dr.document_id,
                        dr.effective_from,
                        dr.effective_until,
                        dr.notes,
                        dr.created_at,
                        d.document_number,
                        d.title,
                        u.username as assigned_by
                    FROM document_roles dr
                    LEFT JOIN documents d ON dr.document_id = d.id
                    JOIN users u ON dr.assigned_by_id = u.id
                    WHERE dr.user_id = :user_id 
                      AND dr.is_deleted = FALSE
                      AND (dr.effective_until IS NULL OR dr.effective_until > NOW())
                    ORDER BY dr.document_id NULLS FIRST, dr.created_at DESC
                """)
                
                result = self.db.execute(query, {'user_id': user_id})
            
            roles = []
            for row in result.fetchall():
                roles.append({
                    'id': row.id,
                    'role': row.role,
                    'document_id': row.document_id,
                    'document_number': row.document_number,
                    'document_title': row.title,
                    'effective_from': row.effective_from,
                    'effective_until': row.effective_until,
                    'notes': row.notes,
                    'created_at': row.created_at,
                    'assigned_by': row.assigned_by,
                    'scope': 'global' if row.document_id is None else 'document'
                })
            
            return roles
            
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {str(e)}")
            return []
    
    def get_document_user_roles(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all user roles for a specific document"""
        try:
            query = text("""
                SELECT 
                    dr.id,
                    dr.user_id,
                    dr.role,
                    dr.effective_from,
                    dr.effective_until,
                    dr.notes,
                    dr.created_at,
                    u.username,
                    u.email,
                    u.first_name,
                    u.last_name,
                    assigned_by.username as assigned_by
                FROM document_roles dr
                JOIN users u ON dr.user_id = u.id
                JOIN users assigned_by ON dr.assigned_by_id = assigned_by.id
                WHERE (dr.document_id = :document_id OR dr.document_id IS NULL)
                  AND dr.is_deleted = FALSE
                  AND (dr.effective_until IS NULL OR dr.effective_until > NOW())
                ORDER BY dr.document_id NULLS FIRST, dr.role, u.username
            """)
            
            result = self.db.execute(query, {'document_id': document_id})
            roles = []
            
            for row in result.fetchall():
                roles.append({
                    'id': row.id,
                    'user_id': row.user_id,
                    'username': row.username,
                    'email': row.email,
                    'full_name': f"{row.first_name or ''} {row.last_name or ''}".strip(),
                    'role': row.role,
                    'effective_from': row.effective_from,
                    'effective_until': row.effective_until,
                    'notes': row.notes,
                    'created_at': row.created_at,
                    'assigned_by': row.assigned_by,
                    'scope': 'global' if row.document_id is None else 'document'
                })
            
            return roles
            
        except Exception as e:
            logger.error(f"Error getting user roles for document {document_id}: {str(e)}")
            return []
    
    def check_user_permission(
        self,
        user_id: int,
        document_id: int,
        required_permission: str
    ) -> bool:
        """Check if user has required permission for a document"""
        try:
            # Get user's highest role for the document
            user_role = self.get_user_highest_role(user_id, document_id)
            
            if not user_role:
                return False
            
            # Check permission hierarchy
            return self._has_permission(user_role, required_permission)
            
        except Exception as e:
            logger.error(f"Error checking permission for user {user_id} on document {document_id}: {str(e)}")
            return False
    
    def get_user_highest_role(
        self,
        user_id: int,
        document_id: Optional[int] = None
    ) -> Optional[str]:
        """Get the highest role a user has for a document or globally"""
        try:
            roles = self.get_user_document_roles(user_id, document_id)
            
            if not roles:
                return None
            
            # Find highest role in hierarchy
            highest_role = None
            highest_index = -1
            
            for role_info in roles:
                role = role_info['role']
                try:
                    role_index = self.ROLE_HIERARCHY.index(role)
                    if role_index > highest_index:
                        highest_index = role_index
                        highest_role = role
                except ValueError:
                    # Role not in hierarchy, skip
                    continue
            
            return highest_role
            
        except Exception as e:
            logger.error(f"Error getting highest role for user {user_id}: {str(e)}")
            return None
    
    def get_users_with_permission(
        self,
        document_id: int,
        required_permission: str
    ) -> List[Dict[str, Any]]:
        """Get all users who have a specific permission for a document"""
        try:
            users_with_role = []
            
            # Get all user roles for the document
            roles = self.get_document_user_roles(document_id)
            
            # Filter users with required permission
            processed_users = set()
            
            for role_info in roles:
                user_id = role_info['user_id']
                
                # Skip if we already processed this user (they might have multiple roles)
                if user_id in processed_users:
                    continue
                
                # Check if user has required permission
                if self.check_user_permission(user_id, document_id, required_permission):
                    users_with_role.append({
                        'user_id': user_id,
                        'username': role_info['username'],
                        'email': role_info['email'],
                        'full_name': role_info['full_name'],
                        'highest_role': self.get_user_highest_role(user_id, document_id),
                        'permission': required_permission
                    })
                    processed_users.add(user_id)
            
            return users_with_role
            
        except Exception as e:
            logger.error(f"Error getting users with permission {required_permission} for document {document_id}: {str(e)}")
            return []
    
    def get_role_statistics(self) -> Dict[str, Any]:
        """Get statistics about role assignments"""
        try:
            stats_query = text("""
                SELECT 
                    role,
                    COUNT(*) as total_assignments,
                    COUNT(CASE WHEN document_id IS NULL THEN 1 END) as global_assignments,
                    COUNT(CASE WHEN document_id IS NOT NULL THEN 1 END) as document_assignments,
                    COUNT(DISTINCT user_id) as unique_users
                FROM document_roles
                WHERE is_deleted = FALSE
                  AND (effective_until IS NULL OR effective_until > NOW())
                GROUP BY role
                ORDER BY 
                    CASE role 
                        WHEN 'admin' THEN 5
                        WHEN 'approver' THEN 4
                        WHEN 'reviewer' THEN 3
                        WHEN 'author' THEN 2
                        WHEN 'viewer' THEN 1
                        ELSE 0
                    END DESC
            """)
            
            result = self.db.execute(stats_query)
            role_stats = {}
            
            for row in result.fetchall():
                role_stats[row.role] = {
                    'total_assignments': row.total_assignments,
                    'global_assignments': row.global_assignments,
                    'document_assignments': row.document_assignments,
                    'unique_users': row.unique_users
                }
            
            # Get overall statistics
            overall_query = text("""
                SELECT 
                    COUNT(*) as total_role_assignments,
                    COUNT(DISTINCT user_id) as total_users_with_roles,
                    COUNT(DISTINCT document_id) as total_documents_with_roles
                FROM document_roles
                WHERE is_deleted = FALSE
                  AND (effective_until IS NULL OR effective_until > NOW())
            """)
            
            overall_result = self.db.execute(overall_query)
            overall_row = overall_result.fetchone()
            
            return {
                'role_breakdown': role_stats,
                'overall': {
                    'total_role_assignments': overall_row.total_role_assignments,
                    'total_users_with_roles': overall_row.total_users_with_roles,
                    'total_documents_with_roles': overall_row.total_documents_with_roles
                },
                'role_hierarchy': self.ROLE_HIERARCHY
            }
            
        except Exception as e:
            logger.error(f"Error getting role statistics: {str(e)}")
            return {}
    
    # Private helper methods
    
    def _has_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if a role has a specific permission"""
        try:
            user_role_index = self.ROLE_HIERARCHY.index(user_role)
            required_role_index = self.ROLE_HIERARCHY.index(required_permission)
            
            # Higher or equal role has permission
            return user_role_index >= required_role_index
            
        except ValueError:
            # Role not found in hierarchy
            return False
    
    def bulk_assign_roles(
        self,
        assignments: List[Dict[str, Any]],
        assigned_by_id: int
    ) -> List[Dict[str, Any]]:
        """Bulk assign multiple roles"""
        results = []
        
        for assignment in assignments:
            try:
                result = self.assign_document_role(
                    user_id=assignment['user_id'],
                    document_id=assignment.get('document_id'),
                    role=assignment['role'],
                    assigned_by_id=assigned_by_id,
                    effective_until=assignment.get('effective_until'),
                    notes=assignment.get('notes', '')
                )
                results.append({'success': True, 'result': result})
            except Exception as e:
                results.append({'success': False, 'error': str(e), 'assignment': assignment})
        
        return results
    
    def get_expiring_roles(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get roles that will expire within the specified number of days"""
        try:
            query = text("""
                SELECT 
                    dr.id,
                    dr.user_id,
                    dr.document_id,
                    dr.role,
                    dr.effective_until,
                    u.username,
                    u.email,
                    d.document_number,
                    d.title
                FROM document_roles dr
                JOIN users u ON dr.user_id = u.id
                LEFT JOIN documents d ON dr.document_id = d.id
                WHERE dr.effective_until IS NOT NULL
                  AND dr.effective_until BETWEEN NOW() AND NOW() + INTERVAL ':days days'
                  AND dr.is_deleted = FALSE
                ORDER BY dr.effective_until ASC
            """)
            
            result = self.db.execute(query, {'days': days_ahead})
            expiring_roles = []
            
            for row in result.fetchall():
                days_until_expiry = (row.effective_until - datetime.now()).days
                
                expiring_roles.append({
                    'role_id': row.id,
                    'user_id': row.user_id,
                    'username': row.username,
                    'email': row.email,
                    'document_id': row.document_id,
                    'document_number': row.document_number,
                    'document_title': row.title,
                    'role': row.role,
                    'effective_until': row.effective_until,
                    'days_until_expiry': days_until_expiry,
                    'scope': 'global' if row.document_id is None else 'document'
                })
            
            return expiring_roles
            
        except Exception as e:
            logger.error(f"Error getting expiring roles: {str(e)}")
            return []