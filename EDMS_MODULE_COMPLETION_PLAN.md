# EDMS Module Completion Plan
**Date:** November 1, 2025  
**Current Status:** Phase 1 Complete - Basic Integration Working  
**Target:** Full QMS Masterplan Compliance

## 🎯 Executive Summary

The EDMS module currently displays 10 documents with basic metadata, but lacks the complete workflow functionality required by the QMS System Masterplan. This plan outlines the development needed to implement:

1. **Document Review & Approval Workflows**
2. **Document Lifecycle Management** 
3. **Role-Based Access Control**
4. **Version Control & Dependencies**
5. **Digital Signatures & Downloads**

## 📊 Current State Analysis

### ✅ **What's Working (Phase 1 Complete)**
- ✅ Basic document listing with 10 sample documents
- ✅ Document types (SOP, Policy, Work Instruction, Form, Manual)
- ✅ Authentication and JWT token system
- ✅ Database schema with documents, document_types tables
- ✅ API endpoints for basic CRUD operations
- ✅ Frontend integration displaying real data

### ❌ **What's Missing (Per QMS Masterplan)**
- ❌ **Document Workflow System** (Review → Approval → Effective)
- ❌ **Role-Based Permissions** (Viewer, Author, Reviewer, Approver, Admin)
- ❌ **Document Status Management** (Draft, Pending Review, Approved, Effective, Superseded)
- ❌ **Version Control & Up-versioning Workflow**
- ❌ **Document Dependencies & Impact Analysis**
- ❌ **File Upload & Download System**
- ❌ **Digital Signatures & Official PDF Generation**
- ❌ **Document Lifecycle Dashboards**
- ❌ **Metadata Placeholder System**

## 🏗️ Development Plan - Phase 2: Core Workflow Implementation

### **Phase 2A: Database Schema Enhancement (Week 1)**

#### **New Tables Required:**
```sql
-- Document workflows
CREATE TABLE document_workflows (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    workflow_type VARCHAR(50) NOT NULL, -- 'review', 'up_version', 'obsolete'
    status VARCHAR(50) NOT NULL, -- 'draft', 'pending_review', 'pending_approval', 'approved'
    initiated_by_id INTEGER REFERENCES users(id),
    current_step VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Workflow steps and assignments
CREATE TABLE workflow_steps (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES document_workflows(id),
    step_type VARCHAR(50) NOT NULL, -- 'review', 'approve'
    assigned_to_id INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'rejected'
    comments TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE
);

-- Document versions
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    version_number VARCHAR(20) NOT NULL,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size BIGINT,
    mime_type VARCHAR(100),
    uploaded_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_current BOOLEAN DEFAULT FALSE
);

-- Document dependencies
CREATE TABLE document_dependencies (
    id SERIAL PRIMARY KEY,
    parent_document_id INTEGER REFERENCES documents(id),
    dependent_document_id INTEGER REFERENCES documents(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(parent_document_id, dependent_document_id)
);

-- Document roles and permissions
CREATE TABLE document_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    document_id INTEGER REFERENCES documents(id),
    role VARCHAR(50) NOT NULL, -- 'viewer', 'author', 'reviewer', 'approver'
    assigned_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### **Enhanced Documents Table:**
```sql
-- Add missing columns to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS workflow_id INTEGER REFERENCES document_workflows(id);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS effective_date DATE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS review_due_date DATE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS superseded_by_id INTEGER REFERENCES documents(id);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS obsolete_date DATE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_source VARCHAR(50) DEFAULT 'original_digital'; -- 'original_digital', 'scanned_original', 'scanned_copy'
ALTER TABLE documents ADD COLUMN IF NOT EXISTS revision_reason TEXT;
```

### **Phase 2B: Backend API Development (Week 2-3)**

#### **Document Workflow Service:**
```python
class DocumentWorkflowService:
    def start_review_workflow(self, document_id: int, reviewer_id: int, user_id: int)
    def start_approval_workflow(self, document_id: int, approver_id: int, user_id: int)
    def start_up_version_workflow(self, document_id: int, reason: str, user_id: int)
    def start_obsolete_workflow(self, document_id: int, reason: str, user_id: int)
    def submit_review(self, workflow_id: int, approved: bool, comments: str, user_id: int)
    def submit_approval(self, workflow_id: int, approved: bool, effective_date: date, user_id: int)
    def terminate_workflow(self, workflow_id: int, reason: str, user_id: int)
```

#### **New API Endpoints:**
```python
# Workflow management
POST /api/v1/documents/{id}/start-review
POST /api/v1/documents/{id}/start-approval  
POST /api/v1/documents/{id}/start-up-version
POST /api/v1/documents/{id}/start-obsolete
POST /api/v1/documents/workflows/{id}/submit-review
POST /api/v1/documents/workflows/{id}/submit-approval
DELETE /api/v1/documents/workflows/{id}/terminate

# File management
POST /api/v1/documents/{id}/upload
GET /api/v1/documents/{id}/download/{type} # original, annotated, official_pdf
GET /api/v1/documents/{id}/versions

# Dependencies
POST /api/v1/documents/{id}/dependencies
GET /api/v1/documents/{id}/dependencies
DELETE /api/v1/documents/{id}/dependencies/{dep_id}

# Role management
POST /api/v1/documents/{id}/roles
GET /api/v1/documents/{id}/roles
PUT /api/v1/documents/{id}/roles/{role_id}
DELETE /api/v1/documents/{id}/roles/{role_id}

# Dashboard
GET /api/v1/documents/dashboard/my-workflows
GET /api/v1/documents/dashboard/pending-actions
```

### **Phase 2C: Frontend Workflow Interface (Week 4)**

#### **Enhanced DocumentsPage Components:**
1. **Document Detail Modal** with workflow actions
2. **Workflow Status Indicators** (badges, progress bars)
3. **Action Buttons** based on user role and document status
4. **Review/Approval Forms** with comments and file upload
5. **Version History Display** with compare functionality
6. **Dependencies Management** interface

#### **New Frontend Components:**
```tsx
// Workflow components
<DocumentWorkflowPanel document={document} currentUser={user} />
<ReviewForm onSubmit={handleReviewSubmit} />
<ApprovalForm onSubmit={handleApprovalSubmit} />
<VersionUploadModal document={document} />
<DependenciesManager document={document} />

// Dashboard components  
<MyWorkflowsDashboard />
<PendingActionsList />
<DocumentStatusCard />
```

## 🏗️ Development Plan - Phase 3: Advanced Features (Week 5-6)

### **Phase 3A: File Management & Digital Signatures**
- **MinIO Integration** for file storage
- **PDF Generation** with metadata annotation
- **Digital Signature Service** integration
- **File Version Control** with checksums

### **Phase 3B: Role-Based Access Control**
- **RBAC Implementation** per QMS Masterplan specifications
- **Permission-based UI** rendering
- **Document-level Role Assignment**
- **Approval Chain Management**

### **Phase 3C: Advanced Workflow Features**
- **Automated Notifications** for pending actions
- **Escalation Rules** for overdue tasks
- **Bulk Operations** for multiple documents
- **Impact Analysis** for dependencies

## 📋 Detailed Implementation Roadmap

### **Week 1: Database Foundation**
- **Day 1-2**: Create workflow tables and relationships
- **Day 3-4**: Enhance documents table with missing columns
- **Day 5**: Populate sample workflow data and test relationships

### **Week 2: Core Workflow Backend**
- **Day 1-2**: Document workflow service implementation
- **Day 3-4**: Review and approval workflow endpoints
- **Day 5**: Up-versioning and obsolete workflow endpoints

### **Week 3: File Management Backend**
- **Day 1-2**: File upload/download service with MinIO
- **Day 3-4**: Version control and dependency management
- **Day 5**: Role-based permission system

### **Week 4: Frontend Integration**
- **Day 1-2**: Document detail modal with workflow actions
- **Day 3-4**: Review and approval forms
- **Day 5**: Dashboard with workflow status

### **Week 5: Advanced Features**
- **Day 1-2**: Digital signature integration
- **Day 3-4**: PDF generation with metadata
- **Day 5**: Notification system

### **Week 6: Testing & Refinement**
- **Day 1-2**: End-to-end workflow testing
- **Day 3-4**: User interface polish and optimization
- **Day 5**: Performance testing and bug fixes

## 🎯 Success Criteria

### **Phase 2 Completion Metrics:**
- ✅ **Document Workflow**: Complete review → approval → effective workflow functional
- ✅ **Role Permissions**: User can only see actions they're authorized for
- ✅ **Status Management**: Documents progress through correct status transitions
- ✅ **File Upload**: Users can upload document files and versions
- ✅ **Dependencies**: Documents can be linked with impact analysis

### **QMS Masterplan Compliance:**
- ✅ **All 5 Document Roles** implemented (Viewer, Author, Reviewer, Approver, Admin)
- ✅ **All 6 Document Types** with proper categorization
- ✅ **All 3 Document Sources** with proper handling
- ✅ **Complete Workflow System** matching masterplan specifications
- ✅ **Digital Signature** capability for official documents

## 🚀 Quick Wins - Immediate Improvements (This Week)

### **Priority 1: Fix Current Page Links**
1. **Document Detail Modal**: Make document titles clickable
2. **View Button**: Implement document detail view
3. **Action Buttons**: Add "Start Review", "Approve" buttons based on status
4. **Status Badges**: Add visual status indicators

### **Priority 2: Basic Workflow Actions**
1. **Status Updates**: Allow manual status changes for testing
2. **Comments System**: Add review comments functionality
3. **User Assignment**: Assign reviewers and approvers
4. **Date Management**: Set effective dates and due dates

### **Priority 3: Enhanced UI**
1. **Workflow Progress**: Visual workflow step indicators
2. **Action Dashboard**: Show pending actions for current user
3. **Document History**: Display revision history
4. **Search & Filter**: Filter by status, type, assigned user

## 📁 File Structure for New Components

```
backend/app/
├── services/
│   ├── document_workflow_service.py
│   ├── file_management_service.py
│   └── digital_signature_service.py
├── models/
│   ├── workflow.py
│   └── document_roles.py
└── api/v1/endpoints/
    ├── document_workflows.py
    └── document_roles.py

frontend/src/
├── components/Documents/
│   ├── DocumentDetailModal.tsx
│   ├── WorkflowPanel.tsx
│   ├── ReviewForm.tsx
│   ├── ApprovalForm.tsx
│   └── DependenciesManager.tsx
├── pages/Documents/
│   ├── DocumentWorkflowPage.tsx
│   └── DocumentDashboard.tsx
└── services/
    ├── documentWorkflowService.ts
    └── fileManagementService.ts
```

## 🎊 Next Steps

1. **Immediate**: Fix current page links and add basic workflow actions (this week)
2. **Phase 2**: Implement core workflow system (weeks 1-4)
3. **Phase 3**: Add advanced features and digital signatures (weeks 5-6)
4. **Integration**: Connect with other QMS modules (TMS, QRM, LIMS)

This plan transforms the current basic document listing into a complete QMS-compliant Electronic Document Management System with full workflow capabilities, role-based access control, and digital signature support.

---

**Ready to begin implementation with Phase 2A: Database Schema Enhancement**