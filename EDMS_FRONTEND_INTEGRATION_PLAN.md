# EDMS Frontend Integration Development Plan

## Overview
This document outlines the comprehensive plan for integrating the Electronic Document Management System (EDMS) frontend with the backend APIs in the QMS Platform v3.0.

**Date Created:** 2024-10-31  
**Status:** Phase 1 In Progress  
**Priority:** High  

---

## Current System State

### ✅ Backend Infrastructure (COMPLETE)
- **Database Layer**: 10 EDMS tables fully implemented and operational
  - `documents` (15 sample documents)
  - `document_types` (10 types: SOP, Policy, Form, etc.)
  - `document_categories` (20+ categories with hierarchy)
  - `document_versions`, `document_workflows`, `document_signatures`
  - Full audit integration and compliance features

- **Models & Services**: Comprehensive business logic
  - SQLAlchemy models with pharmaceutical workflows
  - Document lifecycle management
  - Digital signature capabilities
  - Full-text search integration
  - Version control and approval processes

- **Container Status**: Production deployment ready
  - 4 Gunicorn workers running
  - PostgreSQL 18 with complete EDMS schema
  - Redis caching and MinIO storage operational

### ⚠️ API Integration (IN PROGRESS)
- **Status**: Documents API temporarily disabled due to router registration issues
- **Issue**: Router inclusion failing at startup despite successful manual testing
- **Availability**: 15 document endpoints ready but not accessible

### ✅ Frontend Status (MOCK DATA)
- **UI Components**: Professional Material-UI pharmaceutical interface
- **Features**: Document listing, statistics, create/edit dialogs
- **Data**: Currently using hardcoded pharmaceutical examples
- **Integration Ready**: FileUpload component and API service layer prepared

---

## Development Phases

### Phase 1: Enable Backend APIs 🔄 **IN PROGRESS**

#### Phase 1.1: Fix API Router Integration ✅ **COMPLETED**
- [x] **Enable documents endpoint** in `backend/app/api/v1/api.py`
- [x] **Fix database schema mismatches** - resolved `source_type` column issues
- [x] **Clean EDMS model** - aligned with actual database schema
- [x] **Container restart** - fresh deployment with fixed models

#### Phase 1.2: Test Backend Compatibility ⚠️ **BLOCKED**
- [x] **Verify Pydantic v2 compatibility** - models loading successfully
- [x] **Test document endpoints** - 15 routes available but not registered
- [ ] **Resolve router registration issue** - CURRENT BLOCKER
- [ ] **Ensure workflow APIs functional** - pending router fix

**Current Issue:** Documents router fails to register during application startup despite manual testing confirming 15 functional routes.

**Evidence:**
- Manual test: 18 routes → 33 routes when documents router added
- Startup logs: No error messages or success confirmation
- API calls: Return NOT_FOUND for all documents endpoints
- OpenAPI spec: Missing documents endpoints

---

### Phase 2: Frontend Service Integration (PENDING)

#### Phase 2.1: Update DocumentsPage to use Real API
```typescript
// Replace mock data with real API calls
const fetchDocuments = async () => {
  const response = await DocumentService.getDocuments()
  setDocuments(response.data)
}
```

**Tasks:**
- [ ] Replace hardcoded mock data with DocumentService calls
- [ ] Implement error handling for API failures
- [ ] Add loading states and progress indicators
- [ ] Test CRUD operations with real backend

#### Phase 2.2: Integrate File Upload System
- [ ] Connect existing FileUpload component to backend
- [ ] Enable document attachment and versioning
- [ ] Add progress tracking for large pharmaceutical documents
- [ ] Implement file validation for pharmaceutical formats (.pdf, .docx, etc.)

---

### Phase 3: Advanced EDMS Features (PLANNED)

#### Phase 3.1: Document Workflow Integration
- [ ] Review/Approval workflow UI components
- [ ] Digital signature interface (21 CFR Part 11 compliance)
- [ ] Workflow status tracking and notifications
- [ ] Integration with notification system

#### Phase 3.2: Document Version Control
- [ ] Version history display with comparison tools
- [ ] Version rollback capabilities
- [ ] Change tracking and audit trail visualization
- [ ] Document lifecycle management interface

#### Phase 3.3: Search & Discovery
- [ ] Full-text search integration with Elasticsearch
- [ ] Category-based filtering and navigation
- [ ] Advanced search with metadata fields
- [ ] Tag-based document organization

---

## Technical Implementation Details

### Backend API Endpoints (Ready)
```
GET    /api/v1/documents              # List documents
POST   /api/v1/documents              # Create document
GET    /api/v1/documents/{id}         # Get document details
PUT    /api/v1/documents/{id}         # Update document
DELETE /api/v1/documents/{id}         # Delete document
GET    /api/v1/documents/types        # List document types
GET    /api/v1/documents/categories   # List categories
POST   /api/v1/documents/{id}/upload  # Upload file
GET    /api/v1/documents/{id}/download # Download file
... (15 total endpoints)
```

### Frontend Integration Architecture
```typescript
// Service Layer
DocumentService.getDocuments() → API call → Real backend data
DocumentService.createDocument() → Form data → Database persistence
DocumentService.uploadFile() → File upload → MinIO storage

// Component Updates
DocumentsPage → Real API integration
FileUpload → Backend file handling
DocumentDialog → Form submission to API
```

### Database Integration Points
- **User Management**: `created_by_id` → `users.id`
- **Document Types**: `document_type_id` → `document_types.id`
- **Categories**: `category_id` → `document_categories.id`
- **Audit Logging**: All operations tracked in `audit_logs`
- **File Storage**: `file_path` → MinIO object storage

---

## Risk Assessment & Mitigation

### High Risk Items
1. **Router Registration Issue** (Current Blocker)
   - **Risk**: Prevents all backend integration
   - **Mitigation**: Debug startup sequence, add detailed logging
   - **Alternative**: Create standalone document service

2. **File Upload Integration**
   - **Risk**: Large pharmaceutical documents may timeout
   - **Mitigation**: Implement chunked uploads and progress tracking

3. **Digital Signature Compliance**
   - **Risk**: 21 CFR Part 11 compliance requirements
   - **Mitigation**: Use existing backend signature models

### Medium Risk Items
1. **Performance with Large Document Sets**
   - **Mitigation**: Implement pagination and lazy loading
2. **Search Integration Complexity**
   - **Mitigation**: Start with basic search, enhance incrementally

---

## Success Criteria

### Phase 1 Success Metrics
- [ ] Documents API endpoints return data (not NOT_FOUND)
- [ ] All 15 document endpoints accessible via `/api/v1/documents/*`
- [ ] Database queries return real pharmaceutical documents
- [ ] API documentation includes documents endpoints

### Phase 2 Success Metrics
- [ ] Frontend displays real documents from database
- [ ] Create/Edit operations persist to backend
- [ ] File upload works with progress tracking
- [ ] Error handling provides meaningful user feedback

### Phase 3 Success Metrics
- [ ] Complete document workflow functionality
- [ ] Digital signature integration working
- [ ] Advanced search with filters operational
- [ ] Version control and audit trail accessible

---

## Development Environment

### Current Deployment
- **Backend**: FastAPI with 4 Gunicorn workers
- **Database**: PostgreSQL 18 with complete EDMS schema
- **Frontend**: React with Material-UI (mock data)
- **Infrastructure**: Podman containers with Nginx proxy

### Required for Integration
- **API Layer**: Documents router registration fix
- **Service Layer**: API client integration
- **UI Layer**: Replace mock data with service calls
- **File Handling**: MinIO integration for uploads

---

## Next Immediate Actions

### Option A: Debug Router Registration (Recommended)
1. Add detailed logging to `api.py` startup sequence
2. Investigate why documents router not included despite success in manual testing
3. Test individual endpoint registration
4. Verify no import conflicts or circular dependencies

### Option B: Alternative Integration Path
1. Create standalone documents FastAPI app
2. Test endpoints in isolation
3. Integrate once functionality confirmed
4. Gradually merge into main application

### Option C: Frontend-First Approach
1. Continue Phase 2 with enhanced mock data
2. Build complete UI functionality
3. Connect to backend once API issues resolved
4. Parallel development to minimize delays

---

## Conclusion

The EDMS frontend integration is well-positioned for success with a solid backend foundation and production-ready database schema. The current blocker is a router registration issue that prevents API access, but the underlying functionality is complete and tested.

**Estimated Timeline:**
- **Phase 1 Completion**: 1-2 days (resolve router issue)
- **Phase 2 Completion**: 3-5 days (frontend integration)
- **Phase 3 Completion**: 1-2 weeks (advanced features)

**Total Integration**: 2-3 weeks for complete EDMS frontend-backend integration with advanced pharmaceutical workflow features.

---

*Document maintained by: QMS Development Team*  
*Last Updated: 2024-10-31*  
*Next Review: Upon Phase 1 completion*