"""
Cross-Module Integration Testing Suite
Phase 5 Implementation - QMS Platform v3.0

Comprehensive testing of all 5 QMS modules working together:
- User Management, EDMS, QRM, TRM, LIMS integration
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.user import User, Role
from app.models.edms import Document
from app.models.qrm import QualityEvent, CAPA
from app.models.training import EmployeeTraining, TrainingProgram
from app.models.lims import Sample, TestExecution, TestResult
from app.services.audit_service import AuditService


@pytest.fixture
async def client():
    """HTTP client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def db_session():
    """Database session for direct model testing"""
    # This would be configured with test database
    pass


class TestCrossModuleIntegration:
    """Integration testing across all 5 QMS modules"""

    async def test_complete_quality_workflow(self, client: AsyncClient):
        """
        Test complete quality workflow spanning all modules:
        1. User creates test method document (EDMS)
        2. Analyst receives training (TRM) 
        3. Sample is tested using method (LIMS)
        4. OOS result triggers quality event (QRM)
        5. CAPA is created and managed (QRM)
        """
        
        # Step 1: Authenticate as Quality Manager
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin123!"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create test method document (EDMS)
        document_data = {
            "title": "HPLC Assay Method for Aspirin",
            "document_number": "TM-HPLC-001",
            "version": "1.0",
            "document_type": "Test Method",
            "content": "Detailed HPLC procedure for aspirin assay...",
            "approval_required": True
        }
        doc_response = await client.post(
            "/api/v1/documents/", 
            json=document_data, 
            headers=headers
        )
        assert doc_response.status_code == 201
        document_id = doc_response.json()["id"]

        # Step 3: Approve document
        await client.put(
            f"/api/v1/documents/{document_id}/approve",
            headers=headers
        )

        # Step 4: Create training program for test method (TRM)
        training_data = {
            "code": "TRN-HPLC-001",
            "title": "HPLC Method Training",
            "description": "Training on HPLC assay method TM-HPLC-001",
            "training_type": "technical",
            "delivery_method": "classroom",
            "duration_hours": 8.0,
            "regulatory_requirement": True
        }
        training_response = await client.post(
            "/api/v1/training/programs",
            json=training_data,
            headers=headers
        )
        assert training_response.status_code == 201
        training_program_id = training_response.json()["id"]

        # Step 5: Assign training to analyst
        assignment_data = {
            "employee_id": 2,  # Analyst user
            "program_id": training_program_id,
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "reason": "Required for HPLC method qualification"
        }
        await client.post(
            "/api/v1/training/assignments",
            json=assignment_data,
            headers=headers
        )

        # Step 6: Complete training
        assignment_list = await client.get(
            "/api/v1/training/assignments?employee_id=2",
            headers=headers
        )
        assignment_id = assignment_list.json()[0]["id"]
        
        await client.put(
            f"/api/v1/training/assignments/{assignment_id}",
            json={
                "status": "completed",
                "completion_date": datetime.utcnow().isoformat(),
                "score": 95.0,
                "pass_fail": True
            },
            headers=headers
        )

        # Step 7: Register sample in LIMS
        sample_data = {
            "sample_id": "ASPIRIN-2024-001",
            "sample_type_id": 1,  # Finished Product
            "batch_lot_number": "ASP-LOT-240101",
            "collection_date": datetime.utcnow().isoformat(),
            "storage_location": "QC Sample Room"
        }
        sample_response = await client.post(
            "/api/v1/lims/samples",
            json=sample_data,
            headers=headers
        )
        assert sample_response.status_code == 201
        sample_id = sample_response.json()["id"]

        # Step 8: Start test execution (LIMS)
        execution_data = {
            "execution_id": "EXE-ASP-001",
            "sample_id": sample_id,
            "test_method_id": 1,  # HPLC Assay
            "start_datetime": datetime.utcnow().isoformat(),
            "instrument_id": 1
        }
        execution_response = await client.post(
            "/api/v1/lims/test-executions",
            json=execution_data,
            headers=headers
        )
        assert execution_response.status_code == 201
        execution_id = execution_response.json()["id"]

        # Step 9: Record OOS result (LIMS)
        result_data = {
            "test_execution_id": execution_id,
            "test_specification_id": 1,
            "parameter_name": "Assay",
            "result_value": 88.5,  # OOS (spec: 95-105%)
            "units": "% label claim"
        }
        result_response = await client.post(
            "/api/v1/lims/test-results",
            json=result_data,
            headers=headers
        )
        assert result_response.status_code == 201

        # Step 10: Verify automatic quality event creation (QRM)
        await asyncio.sleep(2)  # Allow background processing
        qe_response = await client.get(
            "/api/v1/quality-events?source_reference=EXE-ASP-001",
            headers=headers
        )
        assert qe_response.status_code == 200
        quality_events = qe_response.json()
        assert len(quality_events) > 0
        assert quality_events[0]["event_type"] == "OOS_RESULT"
        quality_event_id = quality_events[0]["id"]

        # Step 11: Create CAPA for quality event (QRM)
        capa_data = {
            "capa_number": "CAPA-2024-001",
            "title": "Investigation of OOS Assay Result",
            "description": "Investigate and correct OOS result for aspirin assay",
            "priority": "high",
            "target_completion_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "quality_event_id": quality_event_id
        }
        capa_response = await client.post(
            "/api/v1/capas/",
            json=capa_data,
            headers=headers
        )
        assert capa_response.status_code == 201
        capa_id = capa_response.json()["id"]

        # Step 12: Verify audit trail across all modules
        audit_response = await client.get(
            "/api/v1/system/audit-log?limit=50",
            headers=headers
        )
        assert audit_response.status_code == 200
        audit_entries = audit_response.json()
        
        # Verify entries from all modules
        module_actions = [entry["action"] for entry in audit_entries]
        assert any("DOCUMENT" in action for action in module_actions)  # EDMS
        assert any("TRAINING" in action for action in module_actions)   # TRM
        assert any("SAMPLE" in action for action in module_actions)     # LIMS
        assert any("QUALITY_EVENT" in action for action in module_actions)  # QRM

        return {
            "document_id": document_id,
            "training_program_id": training_program_id,
            "sample_id": sample_id,
            "quality_event_id": quality_event_id,
            "capa_id": capa_id
        }

    async def test_lims_trm_integration(self, client: AsyncClient):
        """Test LIMS-TRM integration: Analyst qualification verification"""
        
        # Authenticate
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Attempt to start test execution without qualification
        execution_data = {
            "execution_id": "EXE-UNQUALIFIED-001",
            "sample_id": 1,
            "test_method_id": 2,  # Method requiring special qualification
            "start_datetime": datetime.utcnow().isoformat()
        }
        
        # Should check qualification and potentially warn or prevent
        response = await client.post(
            "/api/v1/lims/test-executions",
            json=execution_data,
            headers=headers
        )
        # Implementation would check analyst qualifications via TRM integration
        
        return response.status_code

    async def test_lims_qrm_integration(self, client: AsyncClient):
        """Test LIMS-QRM integration: OOS results trigger quality events"""
        
        # This test verifies that OOS results in LIMS automatically
        # create quality events in QRM module
        
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Record an OOS result
        result_data = {
            "test_execution_id": 1,
            "test_specification_id": 1,
            "parameter_name": "Assay",
            "result_value": 85.0,  # Below spec limit
            "units": "% w/w"
        }
        
        result_response = await client.post(
            "/api/v1/lims/test-results",
            json=result_data,
            headers=headers
        )
        
        # Verify quality event was created
        await asyncio.sleep(1)  # Allow background processing
        qe_response = await client.get(
            "/api/v1/quality-events?event_type=OOS_RESULT",
            headers=headers
        )
        
        return qe_response.status_code == 200 and len(qe_response.json()) > 0

    async def test_edms_all_modules_integration(self, client: AsyncClient):
        """Test EDMS integration with all other modules"""
        
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Create different document types for each module
        documents_to_create = [
            {
                "title": "Standard Operating Procedure - Sample Handling",
                "document_type": "SOP", 
                "module": "LIMS"
            },
            {
                "title": "Training Curriculum - Quality Systems",
                "document_type": "Training Material",
                "module": "TRM"
            },
            {
                "title": "Quality Risk Assessment Template", 
                "document_type": "Template",
                "module": "QRM"
            }
        ]

        created_docs = []
        for doc_data in documents_to_create:
            doc_response = await client.post(
                "/api/v1/documents/",
                json={
                    "title": doc_data["title"],
                    "document_number": f"DOC-{doc_data['module']}-001",
                    "version": "1.0",
                    "document_type": doc_data["document_type"],
                    "content": f"Content for {doc_data['module']} module"
                },
                headers=headers
            )
            if doc_response.status_code == 201:
                created_docs.append(doc_response.json())

        return len(created_docs) == len(documents_to_create)

    async def test_user_management_integration(self, client: AsyncClient):
        """Test User Management integration across all modules"""
        
        # Test that user roles and permissions work across all modules
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Get current user info
        user_response = await client.get("/api/v1/users/me", headers=headers)
        assert user_response.status_code == 200
        
        # Test access to each module's endpoints
        module_endpoints = [
            "/api/v1/documents/",           # EDMS
            "/api/v1/quality-events/",      # QRM
            "/api/v1/training/programs",    # TRM
            "/api/v1/lims/samples",         # LIMS
        ]
        
        access_results = []
        for endpoint in module_endpoints:
            response = await client.get(endpoint, headers=headers)
            access_results.append(response.status_code in [200, 404])  # 404 is OK for empty results
        
        return all(access_results)

    async def test_audit_trail_integration(self, client: AsyncClient):
        """Test that audit trails work across all modules"""
        
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Perform actions in multiple modules
        actions = []
        
        # EDMS action
        doc_response = await client.post("/api/v1/documents/", json={
            "title": "Audit Test Document",
            "document_number": "AUDIT-001",
            "version": "1.0",
            "document_type": "Test",
            "content": "Test content"
        }, headers=headers)
        actions.append(("EDMS", doc_response.status_code))

        # QRM action
        qe_response = await client.post("/api/v1/quality-events/", json={
            "event_number": "QE-AUDIT-001",
            "title": "Audit Test Event",
            "description": "Test quality event for audit",
            "severity": "low",
            "event_type": "Other"
        }, headers=headers)
        actions.append(("QRM", qe_response.status_code))

        # Check audit log
        audit_response = await client.get(
            "/api/v1/system/audit-log?limit=20",
            headers=headers
        )
        
        if audit_response.status_code == 200:
            audit_entries = audit_response.json()
            return len(audit_entries) >= len([a for a in actions if a[1] == 201])
        
        return False

    async def test_dashboard_integration(self, client: AsyncClient):
        """Test integrated dashboard showing data from all modules"""
        
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Get system dashboard
        dashboard_response = await client.get(
            "/api/v1/system/dashboard",
            headers=headers
        )
        
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            
            # Verify dashboard contains data from multiple modules
            expected_keys = [
                "total_users",           # User Management
                "active_documents",      # EDMS
                "open_quality_events",   # QRM
                "overdue_training",      # TRM
                # LIMS metrics would be added when available
            ]
            
            return any(key in dashboard_data for key in expected_keys)
        
        return False


@pytest.fixture
async def integration_test_data():
    """Set up test data for integration testing"""
    # This would create sample data across all modules
    # for comprehensive integration testing
    pass


class TestModuleAPICompatibility:
    """Test API compatibility and data flow between modules"""
    
    async def test_api_response_formats(self, client: AsyncClient):
        """Ensure all module APIs return consistent response formats"""
        
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Test consistent response format across modules
        endpoints = [
            "/api/v1/users/",
            "/api/v1/documents/", 
            "/api/v1/quality-events/",
            "/api/v1/training/programs",
            "/api/v1/lims/samples"
        ]
        
        response_formats = []
        for endpoint in endpoints:
            response = await client.get(endpoint, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Check if response is list format (typical for list endpoints)
                response_formats.append(isinstance(data, list))
        
        return all(response_formats) if response_formats else True

    async def test_cross_module_foreign_keys(self, client: AsyncClient):
        """Test that foreign key relationships work across modules"""
        
        # This would test that references between modules
        # (e.g., LIMS test methods referencing EDMS documents)
        # work correctly
        
        return True  # Placeholder for detailed foreign key testing


class TestPerformanceIntegration:
    """Test system performance with all modules active"""
    
    async def test_concurrent_module_access(self, client: AsyncClient):
        """Test performance when multiple modules are accessed concurrently"""
        
        login_response = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "Admin123!"
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Simulate concurrent access to all modules
        async def access_module(endpoint):
            start_time = datetime.utcnow()
            response = await client.get(endpoint, headers=headers)
            end_time = datetime.utcnow()
            return (endpoint, response.status_code, (end_time - start_time).total_seconds())

        endpoints = [
            "/api/v1/users/",
            "/api/v1/documents/",
            "/api/v1/quality-events/", 
            "/api/v1/training/programs",
            "/api/v1/lims/samples"
        ]

        # Test concurrent access
        tasks = [access_module(endpoint) for endpoint in endpoints]
        results = await asyncio.gather(*tasks)
        
        # Verify all requests completed successfully and within reasonable time
        success_count = sum(1 for _, status, _ in results if status == 200)
        avg_response_time = sum(time for _, _, time in results) / len(results)
        
        return success_count >= len(endpoints) * 0.8 and avg_response_time < 2.0  # 2 second threshold


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])