# QMS System Tests
# Test system endpoints and health checks

import pytest
from fastapi.testclient import TestClient


class TestSystemEndpoints:
    """Test system management endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        # Check required fields
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "environment" in health_data
        
        # Check status is healthy
        assert health_data["status"] == "healthy"
    
    def test_system_info(self, client: TestClient):
        """Test system information endpoint."""
        response = client.get("/api/v1/system/info")
        
        assert response.status_code == 200
        info_data = response.json()
        
        # Check required fields
        required_fields = ["name", "version", "environment", "compliance", "features"]
        for field in required_fields:
            assert field in info_data
        
        # Check compliance
        assert info_data["compliance"] == "21 CFR Part 11"
        
        # Check features list
        assert isinstance(info_data["features"], list)
        assert len(info_data["features"]) > 0
        
        # Verify expected features
        expected_features = [
            "Electronic Document Management",
            "Quality Record Management",
            "Training Record Management",
            "Laboratory Information Management",
            "Digital Signatures",
            "Audit Trail"
        ]
        
        for feature in expected_features:
            assert feature in info_data["features"]
    
    def test_system_settings_public(self, client: TestClient):
        """Test public system settings endpoint."""
        response = client.get("/api/v1/system/settings")
        
        assert response.status_code == 200
        settings_data = response.json()
        
        # Should be a dictionary
        assert isinstance(settings_data, dict)
        
        # Should not contain sensitive settings
        sensitive_keys = ["password", "secret", "key", "token"]
        for key in settings_data.keys():
            for sensitive in sensitive_keys:
                assert sensitive.lower() not in key.lower()
    
    def test_database_status(self, client: TestClient):
        """Test database status endpoint."""
        response = client.get("/api/v1/system/database/status")
        
        assert response.status_code == 200
        db_status = response.json()
        
        # Check database connection info
        assert "url" in db_status
        
        # Verify password is masked
        assert "***" in db_status["url"]
        assert "password" not in db_status["url"].lower()


class TestApplicationStartup:
    """Test application startup and initialization."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        root_data = response.json()
        
        # Check basic info
        assert "message" in root_data
        assert "version" in root_data
        assert "environment" in root_data
        assert "compliance" in root_data
        
        assert root_data["compliance"] == "21 CFR Part 11"
    
    def test_api_documentation_available(self, client: TestClient):
        """Test that API documentation is available."""
        response = client.get("/api/v1/docs")
        
        # In development, docs should be available
        # In production, might be disabled
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Should return HTML content
            assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema endpoint."""
        response = client.get("/api/v1/openapi.json")
        
        # Should be available in development
        if response.status_code == 200:
            schema = response.json()
            
            # Basic OpenAPI structure
            assert "openapi" in schema
            assert "info" in schema
            assert "paths" in schema
            
            # Check API info
            assert schema["info"]["title"] == "QMS Pharmaceutical System"


class TestSecurityHeaders:
    """Test security headers and middleware."""
    
    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are added to responses."""
        response = client.get("/health")
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Content-Security-Policy"
        ]
        
        for header in security_headers:
            assert header in response.headers
        
        # Check specific values
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS configuration."""
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = client.options("/api/v1/system/info", headers=headers)
        
        # CORS should be handled properly
        assert response.status_code in [200, 204]


class TestPerformance:
    """Test basic performance characteristics."""
    
    def test_response_time_header(self, client: TestClient):
        """Test that response time header is added."""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        # Check for process time header
        assert "X-Process-Time" in response.headers
        
        # Should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
        assert process_time < 1.0  # Should be fast for health check
    
    def test_health_check_performance(self, client: TestClient):
        """Test health check response time."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Health check should be fast
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second


class TestErrorHandling:
    """Test error handling and custom error responses."""
    
    def test_404_handler(self, client: TestClient):
        """Test custom 404 error handler."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        error_data = response.json()
        
        # Check error format
        assert "success" in error_data
        assert error_data["success"] is False
        
        assert "error" in error_data
        assert "code" in error_data["error"]
        assert "message" in error_data["error"]
        
        assert error_data["error"]["code"] == "NOT_FOUND"
    
    def test_422_validation_error(self, client: TestClient):
        """Test validation error handling."""
        # Send invalid JSON to an endpoint that expects valid data
        response = client.post("/api/v1/auth/login", json={"invalid": "data"})
        
        assert response.status_code == 422
        error_data = response.json()
        
        # Should have validation error details
        assert "detail" in error_data


class TestMetrics:
    """Test metrics and monitoring endpoints."""
    
    def test_metrics_endpoint(self, client: TestClient):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        metrics_data = response.json()
        
        # Check basic metrics
        assert "app_name" in metrics_data
        assert "version" in metrics_data
        assert "environment" in metrics_data
        assert "timestamp" in metrics_data


class TestDatabaseConnection:
    """Test database connectivity and health."""
    
    def test_database_connection_in_health(self, client: TestClient):
        """Test that health check includes database status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        # Should indicate healthy database
        assert health_data["status"] == "healthy"
        
        # Components should include database info
        if "components" in health_data:
            assert "database" in health_data["components"]
            assert health_data["components"]["database"]["status"] == "healthy"


class TestComplianceFeatures:
    """Test compliance-related system features."""
    
    def test_audit_trail_enabled(self, client: TestClient):
        """Test that audit trail is enabled and accessible."""
        # This would test audit trail system availability
        # Implementation depends on audit trail API
        pass
    
    def test_cfr_21_part_11_mode(self, client: TestClient):
        """Test that 21 CFR Part 11 mode is enabled."""
        response = client.get("/api/v1/system/settings")
        
        assert response.status_code == 200
        settings = response.json()
        
        # Check for compliance settings
        # Note: This depends on which settings are made public
        # Compliance mode should be indicated somewhere
        pass