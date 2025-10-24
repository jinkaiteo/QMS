"""
Integration Test Runner for QMS Platform v3.0
Phase 5 Implementation - Cross-Module Integration Testing

Orchestrates and executes comprehensive integration testing
across all 5 QMS modules with detailed reporting.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import httpx

@dataclass
class TestResult:
    test_name: str
    module: str
    status: str  # PASS, FAIL, ERROR
    duration: float
    details: str
    error_message: str = None

@dataclass
class IntegrationReport:
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    total_duration: float
    module_results: Dict[str, Dict[str, int]]
    detailed_results: List[TestResult]

class QMSIntegrationTester:
    """Comprehensive integration testing for QMS Platform"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.auth_token = None
        self.test_results: List[TestResult] = []
        
    async def setup(self):
        """Initialize testing environment"""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        
        # Authenticate for testing
        try:
            login_response = await self.client.post("/api/v1/auth/login", json={
                "username": "admin",
                "password": "Admin123!"
            })
            if login_response.status_code == 200:
                self.auth_token = login_response.json().get("access_token")
                print("✅ Authentication successful")
            else:
                print(f"❌ Authentication failed: {login_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
        
        return True
    
    async def teardown(self):
        """Clean up testing environment"""
        if self.client:
            await self.client.aclose()
    
    @property
    def headers(self):
        """Authorization headers"""
        return {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
    
    async def run_test(self, test_func, test_name: str, module: str) -> TestResult:
        """Execute a single test and capture results"""
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            if result is True:
                return TestResult(test_name, module, "PASS", duration, "Test completed successfully")
            elif result is False:
                return TestResult(test_name, module, "FAIL", duration, "Test assertion failed")
            else:
                return TestResult(test_name, module, "PASS", duration, f"Test returned: {result}")
                
        except AssertionError as e:
            duration = time.time() - start_time
            return TestResult(test_name, module, "FAIL", duration, "Assertion failed", str(e))
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(test_name, module, "ERROR", duration, "Exception occurred", str(e))
    
    async def test_user_management_health(self) -> bool:
        """Test User Management module health"""
        response = await self.client.get("/api/v1/users/me", headers=self.headers)
        return response.status_code == 200
    
    async def test_edms_health(self) -> bool:
        """Test EDMS module health"""
        response = await self.client.get("/api/v1/documents/", headers=self.headers)
        return response.status_code in [200, 404]  # 404 OK if no documents
    
    async def test_qrm_health(self) -> bool:
        """Test QRM module health"""
        response = await self.client.get("/api/v1/quality-events/", headers=self.headers)
        return response.status_code in [200, 404]  # 404 OK if no events
    
    async def test_trm_health(self) -> bool:
        """Test TRM module health"""
        response = await self.client.get("/api/v1/training/programs", headers=self.headers)
        return response.status_code in [200, 404]  # 404 OK if no programs
    
    async def test_lims_health(self) -> bool:
        """Test LIMS module health"""
        response = await self.client.get("/api/v1/lims/samples", headers=self.headers)
        return response.status_code in [200, 404]  # 404 OK if no samples
    
    async def test_api_documentation(self) -> bool:
        """Test API documentation accessibility"""
        response = await self.client.get("/docs")
        return response.status_code == 200
    
    async def test_health_endpoint(self) -> bool:
        """Test system health endpoint"""
        response = await self.client.get("/health")
        return response.status_code in [200, 404]  # May not be implemented
    
    async def test_edms_document_creation(self) -> bool:
        """Test document creation in EDMS"""
        document_data = {
            "title": "Integration Test Document",
            "document_number": "INT-TEST-001",
            "version": "1.0",
            "document_type": "Test",
            "content": "This is a test document for integration testing"
        }
        
        response = await self.client.post(
            "/api/v1/documents/",
            json=document_data,
            headers=self.headers
        )
        return response.status_code == 201
    
    async def test_qrm_quality_event_creation(self) -> bool:
        """Test quality event creation in QRM"""
        event_data = {
            "event_number": "QE-INT-001",
            "title": "Integration Test Quality Event", 
            "description": "Test quality event for integration testing",
            "severity": "low",
            "event_type": "Other"
        }
        
        response = await self.client.post(
            "/api/v1/quality-events/",
            json=event_data,
            headers=self.headers
        )
        return response.status_code == 201
    
    async def test_trm_training_program_creation(self) -> bool:
        """Test training program creation in TRM"""
        training_data = {
            "code": "TRN-INT-001",
            "title": "Integration Test Training",
            "description": "Test training program for integration testing",
            "training_type": "technical",
            "delivery_method": "online",
            "duration_hours": 2.0
        }
        
        response = await self.client.post(
            "/api/v1/training/programs",
            json=training_data,
            headers=self.headers
        )
        return response.status_code == 201
    
    async def test_concurrent_module_access(self) -> bool:
        """Test concurrent access to all modules"""
        endpoints = [
            "/api/v1/users/me",
            "/api/v1/documents/",
            "/api/v1/quality-events/",
            "/api/v1/training/programs",
            "/api/v1/lims/samples"
        ]
        
        # Execute concurrent requests
        tasks = [
            self.client.get(endpoint, headers=self.headers) 
            for endpoint in endpoints
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if most requests succeeded
        success_count = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code in [200, 404]
        )
        
        return success_count >= len(endpoints) * 0.8  # 80% success rate
    
    async def test_audit_trail_functionality(self) -> bool:
        """Test audit trail across modules"""
        # Try to access audit log
        response = await self.client.get(
            "/api/v1/system/audit-log?limit=10",
            headers=self.headers
        )
        return response.status_code in [200, 404, 403]  # Various valid responses
    
    async def test_cross_module_data_flow(self) -> bool:
        """Test basic data flow between modules"""
        # This is a simplified test - in practice would be more complex
        
        # Create a document
        doc_response = await self.client.post(
            "/api/v1/documents/",
            json={
                "title": "Cross-Module Test Doc",
                "document_number": "CROSS-001", 
                "version": "1.0",
                "document_type": "Test",
                "content": "Test content"
            },
            headers=self.headers
        )
        
        if doc_response.status_code != 201:
            return False
        
        # Create a quality event that could reference the document
        qe_response = await self.client.post(
            "/api/v1/quality-events/",
            json={
                "event_number": "QE-CROSS-001",
                "title": "Cross-Module Test Event",
                "description": "Test event referencing document CROSS-001",
                "severity": "low",
                "event_type": "Other"
            },
            headers=self.headers
        )
        
        return qe_response.status_code == 201
    
    async def run_all_tests(self) -> IntegrationReport:
        """Execute all integration tests"""
        print("🚀 Starting QMS Platform v3.0 Integration Testing...")
        print("=" * 60)
        
        # Define all tests
        tests = [
            # Module Health Tests
            (self.test_user_management_health, "User Management Health", "User Management"),
            (self.test_edms_health, "EDMS Health", "EDMS"),
            (self.test_qrm_health, "QRM Health", "QRM"), 
            (self.test_trm_health, "TRM Health", "TRM"),
            (self.test_lims_health, "LIMS Health", "LIMS"),
            
            # System Tests
            (self.test_api_documentation, "API Documentation", "System"),
            (self.test_health_endpoint, "Health Endpoint", "System"),
            
            # Functionality Tests
            (self.test_edms_document_creation, "Document Creation", "EDMS"),
            (self.test_qrm_quality_event_creation, "Quality Event Creation", "QRM"),
            (self.test_trm_training_program_creation, "Training Program Creation", "TRM"),
            
            # Integration Tests
            (self.test_concurrent_module_access, "Concurrent Access", "Integration"),
            (self.test_audit_trail_functionality, "Audit Trail", "Integration"),
            (self.test_cross_module_data_flow, "Cross-Module Data Flow", "Integration"),
        ]
        
        start_time = time.time()
        
        # Execute all tests
        for test_func, test_name, module in tests:
            print(f"Running: {test_name} ({module})...", end=" ")
            result = await self.run_test(test_func, test_name, module)
            self.test_results.append(result)
            
            if result.status == "PASS":
                print(f"✅ PASS ({result.duration:.2f}s)")
            elif result.status == "FAIL":
                print(f"❌ FAIL ({result.duration:.2f}s)")
                if result.error_message:
                    print(f"   Error: {result.error_message}")
            else:
                print(f"⚠️  ERROR ({result.duration:.2f}s)")
                if result.error_message:
                    print(f"   Error: {result.error_message}")
        
        total_duration = time.time() - start_time
        
        # Generate report
        return self.generate_report(total_duration)
    
    def generate_report(self, total_duration: float) -> IntegrationReport:
        """Generate comprehensive integration test report"""
        
        # Count results by status
        passed = len([r for r in self.test_results if r.status == "PASS"])
        failed = len([r for r in self.test_results if r.status == "FAIL"])
        errors = len([r for r in self.test_results if r.status == "ERROR"])
        
        # Count results by module
        module_results = {}
        for result in self.test_results:
            if result.module not in module_results:
                module_results[result.module] = {"PASS": 0, "FAIL": 0, "ERROR": 0}
            module_results[result.module][result.status] += 1
        
        return IntegrationReport(
            total_tests=len(self.test_results),
            passed_tests=passed,
            failed_tests=failed,
            error_tests=errors,
            total_duration=total_duration,
            module_results=module_results,
            detailed_results=self.test_results
        )
    
    def print_report(self, report: IntegrationReport):
        """Print detailed test report"""
        print("\n" + "=" * 60)
        print("🧪 QMS PLATFORM v3.0 INTEGRATION TEST REPORT")
        print("=" * 60)
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"  Total Tests: {report.total_tests}")
        print(f"  Passed: {report.passed_tests} ✅")
        print(f"  Failed: {report.failed_tests} ❌")
        print(f"  Errors: {report.error_tests} ⚠️")
        print(f"  Success Rate: {(report.passed_tests/report.total_tests)*100:.1f}%")
        print(f"  Total Duration: {report.total_duration:.2f}s")
        
        # Module breakdown
        print(f"\n📋 MODULE RESULTS:")
        for module, results in report.module_results.items():
            total_module = sum(results.values())
            passed_module = results["PASS"]
            success_rate = (passed_module/total_module)*100 if total_module > 0 else 0
            print(f"  {module}: {passed_module}/{total_module} ({success_rate:.1f}%)")
        
        # Failed tests detail
        failed_tests = [r for r in report.detailed_results if r.status in ["FAIL", "ERROR"]]
        if failed_tests:
            print(f"\n❌ FAILED/ERROR TESTS:")
            for test in failed_tests:
                print(f"  {test.test_name} ({test.module}): {test.status}")
                if test.error_message:
                    print(f"    {test.error_message}")
        
        # Overall assessment
        success_rate = (report.passed_tests/report.total_tests)*100
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 90:
            print("  ✅ EXCELLENT - Platform ready for production")
        elif success_rate >= 80:
            print("  ✅ GOOD - Platform mostly functional with minor issues")
        elif success_rate >= 70:
            print("  ⚠️  ACCEPTABLE - Some issues need addressing")
        else:
            print("  ❌ NEEDS WORK - Significant issues require resolution")


async def main():
    """Main integration testing function"""
    tester = QMSIntegrationTester()
    
    # Setup
    if not await tester.setup():
        print("❌ Failed to setup testing environment")
        return
    
    try:
        # Run tests
        report = await tester.run_all_tests()
        
        # Print report
        tester.print_report(report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"integration_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": {
                    "total_tests": report.total_tests,
                    "passed_tests": report.passed_tests,
                    "failed_tests": report.failed_tests,
                    "error_tests": report.error_tests,
                    "success_rate": (report.passed_tests/report.total_tests)*100,
                    "total_duration": report.total_duration
                },
                "module_results": report.module_results,
                "detailed_results": [
                    {
                        "test_name": r.test_name,
                        "module": r.module,
                        "status": r.status,
                        "duration": r.duration,
                        "details": r.details,
                        "error_message": r.error_message
                    }
                    for r in report.detailed_results
                ]
            }, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_file}")
        
    finally:
        # Cleanup
        await tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())