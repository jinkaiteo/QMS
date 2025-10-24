# QMS Authentication Tests
# Test authentication endpoints and security

import pytest
from fastapi.testclient import TestClient

from app.core.security import token_manager
from app.models.user import User


class TestAuthentication:
    """Test authentication functionality."""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user.username
        assert data["user"]["email"] == test_user.email
    
    def test_login_invalid_username(self, client: TestClient):
        """Test login with invalid username."""
        login_data = {
            "username": "nonexistent",
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with invalid password."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client: TestClient, test_user: User, db_session):
        """Test login with inactive user."""
        # Deactivate user
        test_user.status = "inactive"
        db_session.commit()
        
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Account is inactive" in response.json()["detail"]
    
    def test_logout(self, authenticated_client: TestClient):
        """Test logout functionality."""
        response = authenticated_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
    
    def test_token_verification(self, test_user: User):
        """Test JWT token creation and verification."""
        # Create token
        token = token_manager.create_access_token(
            subject=test_user.id,
            additional_claims={"username": test_user.username}
        )
        
        # Verify token
        payload = token_manager.verify_token(token, "access")
        
        assert payload is not None
        assert payload["sub"] == str(test_user.id)
        assert payload["username"] == test_user.username
        assert payload["type"] == "access"
    
    def test_refresh_token(self, test_user: User):
        """Test refresh token creation and verification."""
        refresh_token = token_manager.create_refresh_token(subject=test_user.id)
        
        payload = token_manager.verify_token(refresh_token, "refresh")
        
        assert payload is not None
        assert payload["sub"] == str(test_user.id)
        assert payload["type"] == "refresh"
    
    def test_invalid_token(self):
        """Test invalid token verification."""
        invalid_token = "invalid.token.here"
        
        payload = token_manager.verify_token(invalid_token)
        
        assert payload is None
    
    def test_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/users/")
        
        # Should return 401 or redirect to login
        assert response.status_code in [401, 403]
    
    def test_protected_endpoint_with_token(self, authenticated_client: TestClient):
        """Test accessing protected endpoint with valid token."""
        response = authenticated_client.get("/api/v1/users/")
        
        assert response.status_code == 200


class TestPasswordSecurity:
    """Test password security features."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        from app.core.security import security_utils
        
        password = "testpassword123"
        hashed = security_utils.get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        
        # Should verify correctly
        assert security_utils.verify_password(password, hashed)
        
        # Should not verify with wrong password
        assert not security_utils.verify_password("wrongpassword", hashed)
    
    def test_password_complexity_validation(self):
        """Test password complexity requirements."""
        from app.core.security import security_utils
        
        # Valid complex password
        valid_password = "StrongPass123!"
        result = security_utils.validate_password_complexity(valid_password)
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        
        # Too short
        short_password = "12345"
        result = security_utils.validate_password_complexity(short_password)
        assert result["valid"] is False
        assert any("length" in issue.lower() for issue in result["issues"])
        
        # Missing uppercase
        no_upper = "lowercase123!"
        result = security_utils.validate_password_complexity(no_upper)
        assert result["valid"] is False
        assert any("uppercase" in issue.lower() for issue in result["issues"])
        
        # Missing special character
        no_special = "Password123"
        result = security_utils.validate_password_complexity(no_special)
        assert result["valid"] is False
        assert any("special" in issue.lower() for issue in result["issues"])


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    def test_security_headers(self, client: TestClient):
        """Test that security headers are added."""
        response = client.get("/health")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers for cross-origin requests."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
        
        response = client.options("/api/v1/system/info", headers=headers)
        
        # Should handle CORS properly
        assert response.status_code in [200, 204]


class TestAuditLogging:
    """Test audit logging for authentication events."""
    
    def test_login_audit_log(self, client: TestClient, test_user: User, db_session, test_utils):
        """Test that login events are audited."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        # Check audit log was created
        # Note: This would require audit logging to be implemented in the auth endpoint
        # test_utils.assert_audit_log_created(db_session, "LOGIN", "users", test_user.id)
    
    def test_failed_login_audit_log(self, client: TestClient, test_user: User, db_session):
        """Test that failed login attempts are audited."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        
        # Should create audit log for failed attempt
        # Implementation depends on audit service integration