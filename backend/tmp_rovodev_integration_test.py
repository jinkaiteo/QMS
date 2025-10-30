#!/usr/bin/env python3
"""
Day 10 Integration Testing - QMS Organization Management
Simplified mock backend for testing frontend integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
from typing import List, Dict, Any

app = FastAPI(title="QMS Integration Test API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_departments = [
    {
        "id": 1,
        "uuid": "dept-001",
        "name": "Quality Assurance",
        "description": "Ensures product quality and compliance",
        "department_code": "QA",
        "department_type": "quality",
        "hierarchy_level": 0,
        "hierarchy_path": "1",
        "location": "Building A, Floor 2",
        "cost_center": "CC-QA-001",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "user_count": 15,
        "department_head": {
            "id": 1,
            "full_name": "Dr. Sarah Johnson",
            "job_title": "QA Director",
            "profile_picture_url": None
        },
        "children": [
            {
                "id": 2,
                "uuid": "dept-002",
                "name": "QA Testing",
                "description": "Product testing and validation",
                "department_code": "QAT",
                "department_type": "quality",
                "hierarchy_level": 1,
                "hierarchy_path": "1.2",
                "location": "Building A, Floor 2, Room 201",
                "cost_center": "CC-QA-002",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "user_count": 8,
                "department_head": {
                    "id": 2,
                    "full_name": "Mike Chen",
                    "job_title": "QA Testing Manager",
                    "profile_picture_url": None
                },
                "children": []
            }
        ]
    },
    {
        "id": 3,
        "uuid": "dept-003",
        "name": "Manufacturing",
        "description": "Production and manufacturing operations",
        "department_code": "MFG",
        "department_type": "operational",
        "hierarchy_level": 0,
        "hierarchy_path": "3",
        "location": "Building B",
        "cost_center": "CC-MFG-001",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "user_count": 25,
        "department_head": {
            "id": 3,
            "full_name": "Robert Smith",
            "job_title": "Manufacturing Director",
            "profile_picture_url": None
        },
        "children": [
            {
                "id": 4,
                "uuid": "dept-004",
                "name": "Production Line A",
                "description": "Primary production line",
                "department_code": "PLA",
                "department_type": "operational",
                "hierarchy_level": 1,
                "hierarchy_path": "3.4",
                "location": "Building B, Floor 1",
                "cost_center": "CC-MFG-002",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "user_count": 12,
                "department_head": {
                    "id": 4,
                    "full_name": "Lisa Wang",
                    "job_title": "Production Supervisor",
                    "profile_picture_url": None
                },
                "children": []
            }
        ]
    }
]

mock_roles = [
    {"id": 1, "name": "quality_manager", "display_name": "Quality Manager", "permissions": ["quality.manage", "documents.approve"]},
    {"id": 2, "name": "qa_analyst", "display_name": "QA Analyst", "permissions": ["quality.view", "tests.execute"]},
    {"id": 3, "name": "production_supervisor", "display_name": "Production Supervisor", "permissions": ["production.manage", "users.supervise"]},
    {"id": 4, "name": "technician", "display_name": "Technician", "permissions": ["equipment.operate", "tests.execute"]},
]

mock_users = [
    {"id": 1, "full_name": "Dr. Sarah Johnson", "job_title": "QA Director", "department": "Quality Assurance"},
    {"id": 2, "full_name": "Mike Chen", "job_title": "QA Testing Manager", "department": "QA Testing"},
    {"id": 3, "full_name": "Robert Smith", "job_title": "Manufacturing Director", "department": "Manufacturing"},
    {"id": 4, "full_name": "Lisa Wang", "job_title": "Production Supervisor", "department": "Production Line A"},
    {"id": 5, "full_name": "Anna Davis", "job_title": "QA Analyst", "department": "Quality Assurance"},
]

mock_assignments = []

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Department Hierarchy Endpoints
@app.get("/v1/organization/departments/hierarchy")
async def get_department_hierarchy():
    """Get department hierarchy for integration testing"""
    return {
        "data": mock_departments,
        "success": True,
        "message": "Department hierarchy retrieved successfully"
    }

@app.get("/v1/organization/departments")
async def get_departments():
    """Get all departments"""
    flat_departments = []
    
    def flatten_departments(dept_list):
        for dept in dept_list:
            dept_copy = dept.copy()
            children = dept_copy.pop('children', [])
            flat_departments.append(dept_copy)
            if children:
                flatten_departments(children)
    
    flatten_departments(mock_departments)
    
    return {
        "data": flat_departments,
        "success": True,
        "message": "Departments retrieved successfully"
    }

@app.post("/v1/organization/departments")
async def create_department(department_data: dict):
    """Create new department"""
    new_dept = {
        "id": len(mock_departments) + 10,
        "uuid": f"dept-{len(mock_departments) + 10:03d}",
        "name": department_data.get("name"),
        "description": department_data.get("description", ""),
        "department_code": department_data.get("department_code", ""),
        "department_type": department_data.get("department_type", "operational"),
        "hierarchy_level": 0,
        "hierarchy_path": str(len(mock_departments) + 10),
        "location": department_data.get("location", ""),
        "cost_center": department_data.get("cost_center", ""),
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "user_count": 0,
        "department_head": None,
        "children": []
    }
    
    mock_departments.append(new_dept)
    
    return {
        "data": new_dept,
        "success": True,
        "message": "Department created successfully"
    }

@app.get("/v1/organization/departments/{dept_id}")
async def get_department(dept_id: int):
    """Get specific department"""
    # Search in flat structure
    def find_department(dept_list, target_id):
        for dept in dept_list:
            if dept["id"] == target_id:
                return dept
            if dept.get("children"):
                result = find_department(dept["children"], target_id)
                if result:
                    return result
        return None
    
    department = find_department(mock_departments, dept_id)
    
    if not department:
        return {"success": False, "message": "Department not found"}, 404
    
    return {
        "data": department,
        "success": True,
        "message": "Department retrieved successfully"
    }

# Role Management Endpoints
@app.get("/v1/organization/roles")
async def get_roles():
    """Get all roles"""
    return {
        "data": mock_roles,
        "success": True,
        "message": "Roles retrieved successfully"
    }

@app.get("/v1/organization/users")
async def get_users():
    """Get all users"""
    return {
        "data": mock_users,
        "success": True,
        "message": "Users retrieved successfully"
    }

@app.get("/v1/organization/departments/{dept_id}/roles")
async def get_department_roles(dept_id: int):
    """Get role assignments for department"""
    dept_assignments = [a for a in mock_assignments if a.get("department_id") == dept_id]
    return {
        "data": dept_assignments,
        "success": True,
        "message": "Department roles retrieved successfully"
    }

@app.post("/v1/organization/departments/{dept_id}/roles")
async def assign_role(dept_id: int, assignment_data: dict):
    """Assign role to user in department"""
    new_assignment = {
        "id": len(mock_assignments) + 1,
        "department_id": dept_id,
        "role_id": assignment_data.get("role_id"),
        "user_id": assignment_data.get("user_id"),
        "valid_from": assignment_data.get("valid_from", datetime.now().isoformat()),
        "valid_until": assignment_data.get("valid_until"),
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "department": next((d for d in mock_departments if d["id"] == dept_id), None),
        "role": next((r for r in mock_roles if r["id"] == assignment_data.get("role_id")), None),
        "user": next((u for u in mock_users if u["id"] == assignment_data.get("user_id")), None)
    }
    
    mock_assignments.append(new_assignment)
    
    return {
        "data": new_assignment,
        "success": True,
        "message": "Role assigned successfully"
    }

@app.delete("/v1/organization/departments/{dept_id}/roles/{role_id}/users/{user_id}")
async def revoke_role(dept_id: int, role_id: int, user_id: int):
    """Revoke role assignment"""
    global mock_assignments
    mock_assignments = [
        a for a in mock_assignments 
        if not (a.get("department_id") == dept_id and 
                a.get("role_id") == role_id and 
                a.get("user_id") == user_id)
    ]
    
    return {
        "success": True,
        "message": "Role revoked successfully"
    }

if __name__ == "__main__":
    print("🚀 Starting QMS Integration Test Backend...")
    print("📍 API will be available at: http://localhost:8000")
    print("📍 API Docs at: http://localhost:8000/docs")
    print("🔗 Testing frontend integration with: http://localhost:3002")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )