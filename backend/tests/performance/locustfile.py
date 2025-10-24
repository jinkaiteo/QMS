# QMS Performance Tests
# Locust load testing configuration

from locust import HttpUser, task, between
import json
import random


class QMSUser(HttpUser):
    """Simulated QMS user for load testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts. Login and get token."""
        self.login()
    
    def login(self):
        """Login and store authentication token."""
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        with self.client.post("/api/v1/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    @task(3)
    def view_system_info(self):
        """View system information."""
        self.client.get("/api/v1/system/info")
    
    @task(2)
    def check_health(self):
        """Check system health."""
        self.client.get("/health")
    
    @task(1)
    def view_users(self):
        """View users list."""
        self.client.get("/api/v1/users/")
    
    @task(1)
    def view_user_profile(self):
        """View specific user profile."""
        user_id = random.randint(1, 10)
        with self.client.get(f"/api/v1/users/{user_id}", catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # 404 is expected for non-existent users
    
    @task(1)
    def view_system_settings(self):
        """View system settings."""
        self.client.get("/api/v1/system/settings")


class AdminUser(HttpUser):
    """Simulated admin user with higher privileges."""
    
    wait_time = between(2, 5)
    weight = 1  # Lower weight means fewer admin users
    
    def on_start(self):
        """Login as admin user."""
        self.login_admin()
    
    def login_admin(self):
        """Login with admin credentials."""
        login_data = {
            "username": "sysadmin",
            "password": "Admin123!"
        }
        
        with self.client.post("/api/v1/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                response.success()
            else:
                response.failure(f"Admin login failed: {response.status_code}")
    
    @task(2)
    def create_user(self):
        """Create a new user."""
        user_data = {
            "username": f"loadtest_user_{random.randint(1000, 9999)}",
            "email": f"loadtest_{random.randint(1000, 9999)}@example.com",
            "password": "LoadTest123!",
            "first_name": "Load",
            "last_name": "Test"
        }
        
        self.client.post("/api/v1/users/", json=user_data)
    
    @task(1)
    def check_database_status(self):
        """Check database status."""
        self.client.get("/api/v1/system/database/status")
    
    @task(1)
    def view_all_users(self):
        """View all users with pagination."""
        limit = random.choice([10, 20, 50])
        skip = random.randint(0, 100)
        self.client.get(f"/api/v1/users/?limit={limit}&skip={skip}")


class APIStressTest(HttpUser):
    """Stress testing for API endpoints."""
    
    wait_time = between(0.1, 0.5)  # Faster requests for stress testing
    weight = 2
    
    @task(5)
    def rapid_health_checks(self):
        """Rapid health check requests."""
        self.client.get("/health")
    
    @task(3)
    def rapid_system_info(self):
        """Rapid system info requests."""
        self.client.get("/api/v1/system/info")
    
    @task(1)
    def concurrent_root_access(self):
        """Concurrent root endpoint access."""
        self.client.get("/")


# Custom test scenarios
class DatabaseLoadTest(HttpUser):
    """Test database performance under load."""
    
    wait_time = between(1, 2)
    
    def on_start(self):
        """Login for database tests."""
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data.get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def search_users(self):
        """Search users to test database queries."""
        self.client.get("/api/v1/users/?limit=50")
    
    @task(2)
    def get_user_details(self):
        """Get detailed user information."""
        user_id = random.randint(1, 5)
        self.client.get(f"/api/v1/users/{user_id}")
    
    @task(1)
    def database_status_check(self):
        """Check database connection status."""
        self.client.get("/api/v1/system/database/status")