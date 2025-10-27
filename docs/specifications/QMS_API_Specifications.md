# QMS System - API Specifications

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication & Security](#authentication--security)
3. [Common Response Patterns](#common-response-patterns)
4. [User Management APIs](#user-management-apis)
5. [EDMS APIs](#edms-apis)
6. [QRM APIs](#qrm-apis)
7. [Error Handling](#error-handling)

## API Overview

### Base URL Structure
```
Production:  https://qms.company.com/api/v1
Staging:     https://qms-staging.company.com/api/v1
Development: http://localhost:8000/api/v1
```

### API Versioning
- **Current Version**: v1
- **Version Header**: `Accept: application/json; version=1.0`
- **URL Versioning**: `/api/v1/`

### Request/Response Format
- **Content Type**: `application/json`
- **Character Encoding**: UTF-8
- **Date Format**: ISO 8601 (`2024-01-15T10:30:00Z`)

## Authentication & Security

### JWT Authentication
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "john.doe",
    "password": "securePassword123!",
    "mfa_code": "123456"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": 123,
        "username": "john.doe",
        "email": "john.doe@company.com",
        "full_name": "John Doe",
        "roles": ["edms_author", "quality_responsible"],
        "permissions": {
            "edms": ["read", "write"],
            "qrm": ["read", "write"]
        }
    }
}
```

### Token Refresh
```http
POST /api/v1/auth/refresh
Content-Type: application/json
Authorization: Bearer <refresh_token>

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Authorization Header
```http
Authorization: Bearer <access_token>
```

### Permission Requirements
Each endpoint specifies required permissions:
- **Module**: `edms`, `qrm`, `trm`, `lims`, `system`
- **Permission**: `read`, `write`, `review`, `approve`, `admin`

## Common Response Patterns

### Success Response
```json
{
    "success": true,
    "data": { /* response data */ },
    "message": "Operation completed successfully",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Paginated Response
```json
{
    "success": true,
    "data": {
        "items": [ /* array of items */ ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 150,
            "pages": 8,
            "has_next": true,
            "has_prev": false
        }
    },
    "message": "Data retrieved successfully"
}
```

### Error Response
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field": "email",
            "issue": "Invalid email format"
        }
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## User Management APIs

### User Authentication

#### Login
```http
POST /api/v1/auth/login
```
**Request Body:**
```json
{
    "username": "string",
    "password": "string",
    "mfa_code": "string (optional)"
}
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

#### Get Current User Profile
```http
GET /api/v1/auth/profile
Authorization: Bearer <token>
```

### User Management

#### List Users
```http
GET /api/v1/users?page=1&per_page=20&search=john&department_id=5
Authorization: Bearer <token>
Required Permission: users:read
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `search` (string): Search in name, username, email
- `department_id` (int): Filter by department
- `is_active` (boolean): Filter by active status
- `role` (string): Filter by role name

#### Get User Details
```http
GET /api/v1/users/{user_id}
Authorization: Bearer <token>
Required Permission: users:read
```

#### Create User
```http
POST /api/v1/users
Authorization: Bearer <token>
Required Permission: users:write
```

**Request Body:**
```json
{
    "username": "jane.smith",
    "email": "jane.smith@company.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "employee_id": "EMP001234",
    "department_id": 5,
    "manager_id": 10,
    "phone": "+1-555-0123",
    "password": "temporaryPassword123!",
    "must_change_password": true,
    "roles": ["edms_viewer", "quality_responsible"]
}
```

#### Update User
```http
PUT /api/v1/users/{user_id}
Authorization: Bearer <token>
Required Permission: users:write
```

#### Deactivate User
```http
DELETE /api/v1/users/{user_id}
Authorization: Bearer <token>
Required Permission: users:admin
```

### Role Management

#### List Roles
```http
GET /api/v1/roles?module=edms
Authorization: Bearer <token>
Required Permission: users:read
```

#### Assign Role to User
```http
POST /api/v1/users/{user_id}/roles
Authorization: Bearer <token>
Required Permission: users:admin
```

**Request Body:**
```json
{
    "role_id": 15,
    "valid_from": "2024-01-15T00:00:00Z",
    "valid_until": "2024-12-31T23:59:59Z"
}
```

## EDMS APIs

### Document Management

#### List Documents
```http
GET /api/v1/edms/documents?page=1&per_page=20&status=approved&document_type=sop
Authorization: Bearer <token>
Required Permission: edms:read
```

**Query Parameters:**
- `page`, `per_page`: Pagination
- `search`: Full-text search in title, description
- `document_type`: Filter by document type
- `status`: Filter by status
- `author_id`: Filter by author
- `category_id`: Filter by category
- `created_from`, `created_to`: Date range filters
- `tags`: Filter by tags (array)

**Response:**
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": 123,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "document_number": "SOP-LAB-001",
                "title": "Sample Preparation Procedure",
                "description": "Standard procedure for laboratory sample preparation",
                "document_type": {
                    "id": 4,
                    "name": "Standard Operating Procedure",
                    "code": "SOP"
                },
                "status": "approved",
                "current_version": "2.1",
                "author": {
                    "id": 45,
                    "full_name": "Dr. Sarah Johnson",
                    "username": "sarah.johnson"
                },
                "approved_date": "2024-01-10T15:30:00Z",
                "effective_date": "2024-01-15T00:00:00Z",
                "next_review_date": "2025-01-15",
                "tags": ["laboratory", "sample", "procedure"],
                "created_at": "2024-01-05T09:00:00Z",
                "updated_at": "2024-01-10T15:30:00Z"
            }
        ],
        "pagination": { /* pagination info */ }
    }
}
```

#### Get Document Details
```http
GET /api/v1/edms/documents/{document_id}
Authorization: Bearer <token>
Required Permission: edms:read
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 123,
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "document_number": "SOP-LAB-001",
        "title": "Sample Preparation Procedure",
        "description": "Detailed procedure for laboratory sample preparation...",
        "document_type": { /* document type details */ },
        "category": { /* category details */ },
        "source_type": "original_digital",
        "status": "approved",
        "current_version": {
            "id": 456,
            "version_number": "2.1",
            "major_version": 2,
            "minor_version": 1,
            "file_name": "SOP-LAB-001_v2.1.docx",
            "file_size": 524288,
            "file_mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "page_count": 15,
            "author": { /* author details */ },
            "reviewer": { /* reviewer details */ },
            "approver": { /* approver details */ },
            "reviewed_at": "2024-01-08T14:20:00Z",
            "approved_at": "2024-01-10T15:30:00Z",
            "effective_date": "2024-01-15",
            "status": "approved"
        },
        "versions": [ /* array of all versions */ ],
        "dependencies": [ /* array of document dependencies */ ],
        "workflow": { /* current workflow status */ },
        "signatures": [ /* array of digital signatures */ ],
        "metadata": {
            "keywords": ["laboratory", "sample", "preparation"],
            "tags": ["sop", "lab", "validated"],
            "custom_fields": {}
        }
    }
}
```

#### Create Document
```http
POST /api/v1/edms/documents
Authorization: Bearer <token>
Required Permission: edms:write
Content-Type: multipart/form-data
```

**Form Data:**
```
document_data: {
    "title": "New Laboratory Procedure",
    "description": "Description of the new procedure",
    "document_type_id": 4,
    "category_id": 8,
    "source_type": "original_digital",
    "keywords": ["laboratory", "new", "procedure"],
    "tags": ["sop", "lab"]
}
file: [binary file data]
```

#### Upload New Version
```http
POST /api/v1/edms/documents/{document_id}/versions
Authorization: Bearer <token>
Required Permission: edms:write
Content-Type: multipart/form-data
```

### Document Workflows

#### Start Review Workflow
```http
POST /api/v1/edms/documents/{document_id}/workflow/review
Authorization: Bearer <token>
Required Permission: edms:write
```

**Request Body:**
```json
{
    "reviewer_id": 67,
    "due_date": "2024-01-20T23:59:59Z",
    "priority": "normal",
    "comments": "Please review for technical accuracy"
}
```

#### Submit Review
```http
POST /api/v1/edms/workflows/{workflow_id}/review
Authorization: Bearer <token>
Required Permission: edms:review
```

**Request Body:**
```json
{
    "decision": "approve", // approve, approve_with_changes, reject
    "overall_comments": "Document reviewed and approved",
    "comments": [
        {
            "page_number": 3,
            "line_number": 15,
            "section": "Section 2.3",
            "comment_text": "Consider adding more detail here",
            "comment_type": "suggestion"
        }
    ]
}
```

### Document Downloads

#### Download Original Document
```http
GET /api/v1/edms/documents/{document_id}/versions/{version_id}/download?type=original
Authorization: Bearer <token>
Required Permission: edms:read
```

#### Download Official PDF
```http
GET /api/v1/edms/documents/{document_id}/versions/{version_id}/download?type=official_pdf
Authorization: Bearer <token>
Required Permission: edms:read
```

**Response Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="SOP-LAB-001_v2.1_Official.pdf"
Content-Length: 1048576
X-Document-Hash: sha256:abc123def456...
X-Digital-Signature: present
```

This covers the core API specifications for authentication, user management, and EDMS. Would you like me to continue with the QRM APIs and remaining sections?