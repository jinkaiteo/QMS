# QMS Test Configuration
# Pytest configuration and fixtures

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User, Organization, Department, Role
from app.core.security import security_utils


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_organization(db_session):
    """Create a test organization."""
    org = Organization(
        name="Test Pharma Inc",
        code="TEST",
        email="test@pharma.com"
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_department(db_session, test_organization):
    """Create a test department."""
    dept = Department(
        organization_id=test_organization.id,
        name="Quality Assurance",
        code="QA",
        description="Quality assurance department"
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


@pytest.fixture
def test_role(db_session):
    """Create a test role."""
    role = Role(
        name="test_user",
        display_name="Test User",
        description="Test user role",
        module="SYSTEM",
        permissions=["read", "write"]
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def test_user(db_session, test_organization, test_department):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=security_utils.get_password_hash("testpassword"),
        first_name="Test",
        last_name="User",
        employee_id="TEST001",
        organization_id=test_organization.id,
        department_id=test_department.id,
        status="active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session, test_organization, test_department):
    """Create a test admin user."""
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=security_utils.get_password_hash("adminpassword"),
        first_name="Admin",
        last_name="User",
        employee_id="ADMIN001",
        organization_id=test_organization.id,
        department_id=test_department.id,
        status="active"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client."""
    # Login and get token
    login_data = {
        "username": test_user.username,
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    token = token_data["access_token"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def sample_data(db_session, test_organization, test_department):
    """Create sample data for testing."""
    # Create multiple users
    users = []
    for i in range(5):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password_hash=security_utils.get_password_hash("password"),
            first_name=f"User{i}",
            last_name="Test",
            employee_id=f"EMP{i:03d}",
            organization_id=test_organization.id,
            department_id=test_department.id,
            status="active"
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    return {
        "users": users,
        "organization": test_organization,
        "department": test_department
    }


# Test utilities
class TestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def create_test_file(content: str = "Test file content", filename: str = "test.txt"):
        """Create a test file for upload testing."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=filename) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def cleanup_test_file(filepath: str):
        """Clean up test file."""
        import os
        if os.path.exists(filepath):
            os.remove(filepath)
    
    @staticmethod
    def assert_audit_log_created(db_session, action: str, table_name: str, user_id: int):
        """Assert that an audit log was created."""
        from app.models.audit import AuditLog
        
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.action == action,
            AuditLog.table_name == table_name,
            AuditLog.user_id == user_id
        ).first()
        
        assert audit_log is not None, f"Audit log not found for {action} on {table_name}"
        return audit_log


@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils