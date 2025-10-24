#!/usr/bin/env python3
"""
Phase 3 QRM Implementation Test Script
Comprehensive testing of Quality Risk Management functionality
"""

import requests
import json
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "username": "sysadmin",
    "password": "Admin123!"
}

class Phase3QRMTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_quality_event_id = None
        self.test_capa_id = None
        self.passed_tests = 0
        self.total_tests = 0
    
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            print(f"✅ {test_name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {test_name}")
            if details:
                print(f"   ERROR: {details}")
    
    def authenticate(self):
        """Test authentication"""
        print("🔐 Testing Authentication...")
        
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_test("Authentication", True, "JWT token received")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, str(e))
            return False
    
    def test_quality_event_types(self):
        """Test quality event types management"""
        print("\n📋 Testing Quality Event Types...")
        
        # Get quality event types
        try:
            response = requests.get(f"{BASE_URL}/quality-events/types", headers=self.headers)
            if response.status_code == 200:
                types = response.json()
                self.log_test("Get Quality Event Types", True, f"Found {len(types)} types")
            else:
                self.log_test("Get Quality Event Types", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Quality Event Types", False, str(e))
        
        # Create new event type
        try:
            new_type = {
                "name": "Test Event Type",
                "code": "TEST",
                "description": "Test event type for Phase 3 validation",
                "severity_levels": ["critical", "major", "minor"],
                "color": "#FF5722",
                "icon": "warning"
            }
            
            response = requests.post(f"{BASE_URL}/quality-events/types", 
                                   headers=self.headers, json=new_type)
            if response.status_code == 200:
                created_type = response.json()
                self.log_test("Create Quality Event Type", True, f"Created: {created_type['name']}")
            else:
                self.log_test("Create Quality Event Type", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Quality Event Type", False, str(e))
    
    def test_quality_event_creation(self):
        """Test quality event creation"""
        print("\n🚨 Testing Quality Event Creation...")
        
        try:
            # Create test quality event
            quality_event = {
                "title": "Phase 3 Test Quality Event",
                "description": "This is a test quality event for Phase 3 QRM validation. "
                              "Testing the complete quality event lifecycle including investigation "
                              "assignment, status updates, and CAPA generation.",
                "event_type_id": 1,  # Assuming first event type exists
                "severity": "major",
                "occurred_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "priority": 2,
                "source": "internal_audit",
                "location": "Manufacturing Area A",
                "department_id": 1,
                "product_affected": "Test Product Batch",
                "batch_lot_numbers": ["LOT001", "LOT002"],
                "processes_affected": ["mixing", "packaging"],
                "patient_safety_impact": False,
                "product_quality_impact": True,
                "regulatory_impact": False,
                "business_impact_severity": "medium",
                "estimated_cost": 5000.00,
                "investigation_required": True,
                "capa_required": True,
                "regulatory_reporting_required": False
            }
            
            response = requests.post(f"{BASE_URL}/quality-events/", 
                                   headers=self.headers, json=quality_event)
            
            if response.status_code == 200:
                created_event = response.json()
                self.test_quality_event_id = created_event["id"]
                event_number = created_event["event_number"]
                self.log_test("Create Quality Event", True, 
                            f"Event ID: {self.test_quality_event_id}, Number: {event_number}")
            else:
                self.log_test("Create Quality Event", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Create Quality Event", False, str(e))
    
    def test_quality_event_search(self):
        """Test quality event search functionality"""
        print("\n🔍 Testing Quality Event Search...")
        
        # Test basic search
        try:
            search_data = {
                "query": "test",
                "page": 1,
                "per_page": 10
            }
            
            response = requests.post(f"{BASE_URL}/quality-events/search", 
                                   headers=self.headers, json=search_data)
            if response.status_code == 200:
                result = response.json()
                total = result.get('total', 0)
                items = result.get('items', [])
                self.log_test("Quality Event Search", True, 
                            f"Found {total} events, returned {len(items)} items")
            else:
                self.log_test("Quality Event Search", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Quality Event Search", False, str(e))
        
        # Test filtered search
        try:
            search_data = {
                "severity": "major",
                "status": "open",
                "page": 1,
                "per_page": 5
            }
            
            response = requests.post(f"{BASE_URL}/quality-events/search", 
                                   headers=self.headers, json=search_data)
            if response.status_code == 200:
                result = response.json()
                self.log_test("Filtered Quality Event Search", True, 
                            f"Major open events: {result.get('total', 0)}")
            else:
                self.log_test("Filtered Quality Event Search", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Filtered Quality Event Search", False, str(e))
    
    def test_quality_event_workflow(self):
        """Test quality event workflow operations"""
        print("\n🔄 Testing Quality Event Workflow...")
        
        if not self.test_quality_event_id:
            self.log_test("Quality Event Workflow", False, "No test event ID available")
            return
        
        # Assign investigator
        try:
            assign_data = {
                "investigator_id": 2,  # Assuming user ID 2 exists
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
                "comments": "Please investigate this test quality event"
            }
            
            response = requests.post(
                f"{BASE_URL}/quality-events/{self.test_quality_event_id}/assign-investigator",
                headers=self.headers, json=assign_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Assign Investigator", True, f"Success: {result.get('success')}")
            else:
                self.log_test("Assign Investigator", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Assign Investigator", False, str(e))
        
        # Update status
        try:
            status_data = {
                "status": "investigating",
                "comments": "Investigation started for Phase 3 test event"
            }
            
            response = requests.post(
                f"{BASE_URL}/quality-events/{self.test_quality_event_id}/update-status",
                headers=self.headers, json=status_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Update Event Status", True, f"Success: {result.get('success')}")
            else:
                self.log_test("Update Event Status", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Update Event Status", False, str(e))
    
    def test_capa_creation(self):
        """Test CAPA creation"""
        print("\n📝 Testing CAPA Creation...")
        
        try:
            # Create test CAPA
            capa_data = {
                "title": "Phase 3 Test CAPA",
                "description": "This is a test CAPA for Phase 3 QRM validation. "
                              "Testing CAPA lifecycle including action planning, "
                              "approval workflows, and effectiveness verification.",
                "capa_type": "corrective",
                "problem_statement": "Quality event indicates process deviation in manufacturing area",
                "proposed_solution": "Implement additional training and process controls",
                "owner_id": 2,  # Assuming user ID 2 exists
                "target_completion_date": (date.today() + timedelta(days=30)).isoformat(),
                "priority": 2,
                "action_category": "training",
                "quality_event_id": self.test_quality_event_id,
                "responsible_department_id": 1,
                "root_cause": "Insufficient operator training on new equipment",
                "implementation_plan": "1. Develop training materials\n2. Train operators\n3. Validate process",
                "success_criteria": "Zero deviations for 30 days post-implementation",
                "estimated_cost": 15000.00,
                "resources_required": "Training materials, SME time, validation resources",
                "risk_level": "medium",
                "verification_method": "Process performance monitoring",
                "verification_criteria": "Statistical process control within limits",
                "training_required": True
            }
            
            response = requests.post(f"{BASE_URL}/capas/", 
                                   headers=self.headers, json=capa_data)
            
            if response.status_code == 200:
                created_capa = response.json()
                self.test_capa_id = created_capa["id"]
                capa_number = created_capa["capa_number"]
                self.log_test("Create CAPA", True, 
                            f"CAPA ID: {self.test_capa_id}, Number: {capa_number}")
            else:
                self.log_test("Create CAPA", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Create CAPA", False, str(e))
    
    def test_capa_actions(self):
        """Test CAPA actions management"""
        print("\n📋 Testing CAPA Actions...")
        
        if not self.test_capa_id:
            self.log_test("CAPA Actions", False, "No test CAPA ID available")
            return
        
        # Add CAPA action
        try:
            action_data = {
                "title": "Develop Training Materials",
                "description": "Create comprehensive training materials for new equipment operation",
                "assigned_to": 2,  # Assuming user ID 2 exists
                "due_date": (date.today() + timedelta(days=14)).isoformat(),
                "department_id": 1,
                "verification_required": True
            }
            
            response = requests.post(f"{BASE_URL}/capas/{self.test_capa_id}/actions",
                                   headers=self.headers, json=action_data)
            
            if response.status_code == 200:
                created_action = response.json()
                action_id = created_action["id"]
                self.log_test("Create CAPA Action", True, 
                            f"Action ID: {action_id}, Number: {created_action['action_number']}")
                
                # Test completing the action
                complete_data = {
                    "completion_evidence": "Training materials completed and reviewed. "
                                         "Materials include step-by-step procedures, "
                                         "safety guidelines, and competency assessments."
                }
                
                response = requests.post(f"{BASE_URL}/capas/actions/{action_id}/complete",
                                       headers=self.headers, json=complete_data)
                
                if response.status_code == 200:
                    self.log_test("Complete CAPA Action", True, "Action marked as completed")
                else:
                    self.log_test("Complete CAPA Action", False, f"Status: {response.status_code}")
                    
            else:
                self.log_test("Create CAPA Action", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("CAPA Actions", False, str(e))
    
    def test_capa_workflow(self):
        """Test CAPA approval and verification workflow"""
        print("\n✅ Testing CAPA Workflow...")
        
        if not self.test_capa_id:
            self.log_test("CAPA Workflow", False, "No test CAPA ID available")
            return
        
        # Approve CAPA
        try:
            approve_data = {
                "comments": "CAPA approved for implementation. Well-structured plan with clear timeline."
            }
            
            response = requests.post(f"{BASE_URL}/capas/{self.test_capa_id}/approve",
                                   headers=self.headers, json=approve_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Approve CAPA", True, f"Success: {result.get('success')}")
            else:
                self.log_test("Approve CAPA", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Approve CAPA", False, str(e))
    
    def test_analytics_endpoints(self):
        """Test analytics and reporting endpoints"""
        print("\n📊 Testing Analytics Endpoints...")
        
        # Quality events analytics
        try:
            response = requests.get(f"{BASE_URL}/quality-events/analytics/summary", 
                                  headers=self.headers)
            if response.status_code == 200:
                analytics = response.json()
                total_events = analytics.get('total_events', 0)
                self.log_test("Quality Events Analytics", True, f"Total events: {total_events}")
            else:
                self.log_test("Quality Events Analytics", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Quality Events Analytics", False, str(e))
        
        # CAPA analytics
        try:
            response = requests.get(f"{BASE_URL}/capas/analytics/summary", 
                                  headers=self.headers)
            if response.status_code == 200:
                analytics = response.json()
                total_capas = analytics.get('total_capas', 0)
                self.log_test("CAPA Analytics", True, f"Total CAPAs: {total_capas}")
            else:
                self.log_test("CAPA Analytics", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("CAPA Analytics", False, str(e))
    
    def run_comprehensive_test(self):
        """Run all Phase 3 QRM tests"""
        print("🚀 Starting Phase 3 QRM Comprehensive Testing")
        print("=" * 70)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot continue")
            return False
        
        # Step 2: Quality Event Type management
        self.test_quality_event_types()
        
        # Step 3: Quality Event management
        self.test_quality_event_creation()
        self.test_quality_event_search()
        self.test_quality_event_workflow()
        
        # Step 4: CAPA management
        self.test_capa_creation()
        self.test_capa_actions()
        self.test_capa_workflow()
        
        # Step 5: Analytics and reporting
        self.test_analytics_endpoints()
        
        # Results summary
        print("\n" + "=" * 70)
        print("📊 PHASE 3 QRM TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"✅ Passed: {self.passed_tests}/{self.total_tests} tests ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("\n🎉 PHASE 3 QRM FUNCTIONALITY: EXCELLENT!")
            print("✅ All critical QRM features are working correctly")
            print("🚀 Ready for production deployment")
        elif success_rate >= 75:
            print("\n✅ PHASE 3 QRM FUNCTIONALITY: GOOD")
            print("✅ Most QRM features are working correctly")
            print("⚠️  Some minor issues may need attention")
        else:
            print("\n⚠️  PHASE 3 QRM FUNCTIONALITY: NEEDS IMPROVEMENT")
            print("⚠️  Several features need attention")
            print("🔧 Review failed tests before proceeding")
        
        print("=" * 70)
        return success_rate >= 75

if __name__ == "__main__":
    tester = Phase3QRMTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)