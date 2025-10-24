# QMS User Management Tests
# Test user CRUD operations and user management functionality

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserStatus


class TestUserManagement:
    """Test user management endpoints."""
    
    def test_get_users_list(self, authenticated_client: TestClient, sample_data):
        """Test getting list of users."""
        response = authenticated_client.get("/api/v1/users/")
        
        assert response.status_code == 200
        users = response.json()
        
        assert isinstance(users, list)
        assert len(users) > 0
        
        # Check user structure
        user = users[0]
        required_fields = ["id", "uuid", "username", "email", "first_name", "last_name"]
        for field in required_fields:
            assert field in user
    
    def test_get_users_pagination(self, authenticated_client: TestClient, sample_data):
        """Test user list pagination."""
        # Test with limit
        response = authenticated_client.get("/api/v1/users/?limit=2")
        assert response.status_code == 200
        users = response.json()
        assert len(users) <= 2
        
        # Test with skip
        response = authenticated_client.get("/api/v1/users/?skip=1&limit=2")
        assert response.status_code == 200
        users = response.json()
        assert len(users) <= 2
    
    def test_get_user_by_id(self, authenticated_client: TestClient, test_user: User):
        """Test getting specific user by ID."""
        response = authenticated_client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        user_data = response.json()
        
        assert user_data["id"] == test_user.id
        assert user_data["username"] == test_user.username
        assert user_data["email"] == test_user.email
        assert user_data["first_name"] == test_user.first_name
        assert user_data["last_name"] == test_user.last_name
    
    def test_get_nonexistent_user(self, authenticated_client: TestClient):
        """Test getting non-existent user."""
        response = authenticated_client.get("/api/v1/users/99999")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_create_user(self, authenticated_client: TestClient, test_organization, test_department):
        """Test creating a new user."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "first_name": "New",
            "last_name": "User",
            "employee_id": "NEW001",
            "organization_id": test_organization.id,
            "department_id": test_department.id,
            "phone": "+1-555-0123"
        }
        
        response = authenticated_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 200
        created_user = response.json()
        
        assert created_user["username"] == user_data["username"]
        assert created_user["email"] == user_data["email"]
        assert created_user["first_name"] == user_data["first_name"]
        assert created_user["last_name"] == user_data["last_name"]
        assert created_user["employee_id"] == user_data["employee_id"]
        assert "password" not in created_user  # Password should not be returned
    
    def test_create_user_duplicate_username(self, authenticated_client: TestClient, test_user: User):
        """Test creating user with duplicate username."""
        user_data = {
            "username": test_user.username,  # Duplicate username
            "email": "different@example.com",
            "password": "Password123!",
            "first_name": "Different",
            "last_name": "User"
        }
        
        response = authenticated_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    def test_create_user_duplicate_email(self, authenticated_client: TestClient, test_user: User):
        """Test creating user with duplicate email."""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,  # Duplicate email
            "password": "Password123!",
            "first_name": "Different",
            "last_name": "User"
        }
        
        response = authenticated_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]
    
    def test_create_user_invalid_data(self, authenticated_client: TestClient):
        """Test creating user with invalid data."""
        # Missing required fields
        user_data = {
            "username": "incomplete"
            # Missing email, password, names
        }
        
        response = authenticated_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_user(self, authenticated_client: TestClient, test_user: User):
        """Test updating user information."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+1-555-9999"
        }
        
        response = authenticated_client.put(f"/api/v1/users/{test_user.id}", json=update_data)
        
        assert response.status_code == 200
        updated_user = response.json()
        
        assert updated_user["first_name"] == update_data["first_name"]
        assert updated_user["last_name"] == update_data["last_name"]
        assert updated_user["phone"] == update_data["phone"]
        
        # Unchanged fields should remain the same
        assert updated_user["username"] == test_user.username
        assert updated_user["email"] == test_user.email
    
    def test_update_nonexistent_user(self, authenticated_client: TestClient):
        """Test updating non-existent user."""
        update_data = {
            "first_name": "Updated"
        }
        
        response = authenticated_client.put("/api/v1/users/99999", json=update_data)
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_delete_user(self, authenticated_client: TestClient, db_session: Session):
        """Test soft deleting a user."""
        # Create a user to delete
        from app.core.security import security_utils
        
        user_to_delete = User(
            username="deleteme",
            email="deleteme@example.com",
            password_hash=security_utils.get_password_hash("password"),
            first_name="Delete",
            last_name="Me",
            status=UserStatus.ACTIVE
        )
        db_session.add(user_to_delete)
        db_session.commit()
        db_session.refresh(user_to_delete)
        
        response = authenticated_client.delete(f"/api/v1/users/{user_to_delete.id}")
        
        assert response.status_code == 200
        assert "User deleted successfully" in response.json()["message"]
        
        # Verify user is soft deleted
        db_session.refresh(user_to_delete)
        assert user_to_delete.is_deleted is True
    
    def test_delete_nonexistent_user(self, authenticated_client: TestClient):
        """Test deleting non-existent user."""
        response = authenticated_client.delete("/api/v1/users/99999")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestUserValidation:
    """Test user data validation."""
    
    def test_email_validation(self, authenticated_client: TestClient):
        """Test email format validation."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",  # Invalid email format
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = authenticated_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("email" in str(error).lower() for error in error_detail)
    
    def test_password_validation(self, authenticated_client: TestClient):
        """Test password validation."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",  # Too short password
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = authenticated_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("password" in str(error).lower() for error in error_detail)


class TestUserSecurity:
    """Test user security features."""
    
    def test_password_not_returned(self, authenticated_client: TestClient, test_user: User):
        """Test that password is never returned in API responses."""
        response = authenticated_client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        user_data = response.json()
        
        # Password fields should not be present
        assert "password" not in user_data
        assert "password_hash" not in user_data
    
    def test_sensitive_fields_protection(self, authenticated_client: TestClient, test_user: User):
        """Test that sensitive fields are protected."""
        response = authenticated_client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        user_data = response.json()
        
        # Sensitive fields should not be exposed
        sensitive_fields = [
            "password_hash", "two_factor_secret", "failed_login_attempts",
            "account_locked_until", "digital_signature_cert"
        ]
        
        for field in sensitive_fields:
            assert field not in user_data


class TestUserRoles:
    """Test user role assignments."""
    
    def test_user_permissions(self, test_user: User, test_role, db_session):
        """Test user permission checking."""
        from app.models.user import UserRole
        
        # Assign role to user
        user_role = UserRole(
            user_id=test_user.id,
            role_id=test_role.id,
            assigned_by=test_user.id
        )
        db_session.add(user_role)
        db_session.commit()
        
        # Refresh user to load relationships
        db_session.refresh(test_user)
        
        # Test permission checking
        assert test_user.has_permission("read", "SYSTEM")
        assert test_user.has_permission("write", "SYSTEM")
        assert not test_user.has_permission("admin", "SYSTEM")
    
    def test_user_full_name_property(self, test_user: User):
        """Test user full name property."""
        expected_name = f"{test_user.first_name} {test_user.last_name}"
        assert test_user.full_name == expected_name
    
    def test_user_is_active_property(self, test_user: User):
        """Test user is_active property."""
        # Active user
        test_user.status = UserStatus.ACTIVE
        assert test_user.is_active is True
        
        # Inactive user
        test_user.status = UserStatus.INACTIVE
        assert test_user.is_active is False
        
        # Deleted user
        test_user.status = UserStatus.ACTIVE
        test_user.is_deleted = True
        assert test_user.is_active is False


class TestUserAuditTrail:
    """Test user-related audit trail functionality."""
    
    def test_user_creation_audit(self, authenticated_client: TestClient, test_utils, db_session):
        """Test that user creation is audited."""
        user_data = {
            "username": "audituser",
            "email": "audit@example.com",
            "password": "Password123!",
            "first_name": "Audit",
            "last_name": "User"
        }
        
        response = authenticated_client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        
        # Check that audit log was created
        # Note: This requires audit service integration
        # test_utils.assert_audit_log_created(db_session, "CREATE", "users", None)
    
    def test_user_update_audit(self, authenticated_client: TestClient, test_user: User, test_utils, db_session):
        """Test that user updates are audited."""
        update_data = {
            "first_name": "UpdatedName"
        }
        
        response = authenticated_client.put(f"/api/v1/users/{test_user.id}", json=update_data)
        assert response.status_code == 200
        
        # Check that audit log was created
        # test_utils.assert_audit_log_created(db_session, "UPDATE", "users", test_user.id)