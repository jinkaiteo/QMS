# 🧪 EDMS Phase 2 UAT (User Acceptance Testing) Plan

**Version**: 1.0  
**Date**: November 2024  
**Status**: Ready for Execution  
**Module**: Electronic Document Management System (EDMS)  
**Phase**: Phase 2 - Complete Document Lifecycle with File Upload

## 📋 UAT Testing Overview

### Testing Objectives
- Validate complete document lifecycle management (Create → Upload → Review → Approve)
- Verify mandatory file upload requirement enforcement
- Confirm document workflow progression and status tracking
- Validate user interface functionality for document operations

### Testing Approach
- **Duration**: 30 minutes
- **Participants**: Business users, document managers, quality reviewers
- **Environment**: Development environment with test data
- **Success Criteria**: 100% test case pass rate for Phase 2 functionality

---

## 🔐 **PREREQUISITE SETUP**

### TC-SETUP-001: System Access Verification
**Priority**: CRITICAL | **Duration**: 2 minutes

**Preconditions**: 
- Frontend accessible at http://localhost:3001
- Backend API running on http://localhost:8000
- Test user credentials available

**Test Steps**:
1. Navigate to http://localhost:3001
2. Login with username: "admin" and password: "admin123"
3. Verify successful login and dashboard access
4. Navigate to Documents module

**Expected Results**:
- ✅ Login successful with valid credentials
- ✅ Dashboard displays user information  
- ✅ Documents module accessible
- ✅ Document list displays with existing documents

---

## 📄 **TEST SUITE 1: DOCUMENT CREATION & METADATA**

### TC-DOC-001: Create New Document (Metadata Only)
**Priority**: HIGH | **Duration**: 5 minutes

**Test Steps**:
1. Click "Create Document" button
2. Fill in document metadata:
   - Title: "UAT Test Document"
   - Document Number: "UAT-001" 
   - Document Type: Select "SOP"
   - Description: "User acceptance testing document"
   - Category: Select "Quality Management"
   - Confidentiality Level: "Internal"
3. Submit the form
4. Verify document appears in document list

**Expected Results**:
- ✅ Create Document modal opens with all fields
- ✅ All dropdown options populated (10 types, 23 categories)
- ✅ Document creation succeeds with 200 OK response
- ✅ New document appears in list with "Draft" status
- ✅ Document assigned auto-generated or specified number

**Test Data**: 
- Document types available: SOP, Policy, Work Instruction, etc.
- Categories available: Quality Management, Manufacturing, etc.

---

## 📁 **TEST SUITE 2: FILE UPLOAD & VALIDATION**

### TC-UPLOAD-001: Mandatory File Upload Validation
**Priority**: HIGH | **Duration**: 5 minutes

**Test Steps**:
1. Click on the newly created document to open details
2. Verify current document status and available actions
3. Look for "Upload File First" button (should be disabled)
4. Look for "Start Review" button (should NOT be available)
5. Note the file upload requirement messaging

**Expected Results**:
- ✅ Document details modal opens
- ✅ Document shows "Draft" status
- ✅ "Upload File First" button visible and disabled
- ✅ "Start Review" button NOT available
- ✅ Clear messaging about file upload requirement
- ✅ "Upload Document File" button prominently displayed

---

### TC-UPLOAD-002: File Upload Functionality
**Priority**: HIGH | **Duration**: 8 minutes

**Test Steps**:
1. Click "Upload Document File" button in document details
2. Verify upload dialog opens
3. Select a test file (PDF, Word, or text file under 50MB)
4. Add upload reason: "UAT testing file upload"
5. Submit file upload
6. Verify upload completion
7. Close upload dialog and return to document details

**Expected Results**:
- ✅ Upload dialog opens with DocumentUpload component
- ✅ File selection interface works (drag-drop or click)
- ✅ File validation accepts appropriate file types
- ✅ Upload progress indicators display
- ✅ Upload completes with success message
- ✅ File stored with proper version tracking
- ✅ Upload dialog closes after successful upload

**Test Files**: 
- PDF document (recommended)
- Word document (.docx)
- Text file (.txt)
- Image file (.png, .jpg)

---

### TC-UPLOAD-003: Workflow Unlock After Upload
**Priority**: HIGH | **Duration**: 3 minutes

**Test Steps**:
1. After successful file upload, reopen document details
2. Check available action buttons
3. Verify "Start Review" button is now available
4. Verify download buttons are now enabled
5. Check document status and version information

**Expected Results**:
- ✅ "Start Review" button now available and enabled
- ✅ "Upload File First" button no longer appears
- ✅ Download buttons enabled for uploaded file
- ✅ Document shows version information (1.0)
- ✅ File metadata visible in document details

---

## 🔄 **TEST SUITE 3: WORKFLOW PROGRESSION**

### TC-WORKFLOW-001: Start Review Process
**Priority**: HIGH | **Duration**: 5 minutes

**Test Steps**:
1. With a document that has an uploaded file, click "Start Review"
2. Verify review workflow initiation
3. Check document status change
4. Verify workflow tracking and assignments

**Expected Results**:
- ✅ "Start Review" button triggers workflow initiation
- ✅ Document status changes from "Draft" to "Pending Review"
- ✅ Success message confirms workflow started
- ✅ Document list reflects status change
- ✅ Reviewer assignment successful (self-assigned for testing)

---

### TC-WORKFLOW-002: Review Process Execution
**Priority**: MEDIUM | **Duration**: 5 minutes

**Test Steps**:
1. Navigate to document in "Pending Review" status
2. Go to "Workflow" tab in document details
3. Add review comments
4. Submit review approval
5. Verify status progression

**Expected Results**:
- ✅ Workflow tab shows review interface
- ✅ Comment field available for reviewer input
- ✅ Review submission successful
- ✅ Document status progresses to next stage
- ✅ Workflow history tracked and visible

---

## 📊 **TEST SUITE 4: SYSTEM VALIDATION**

### TC-SYSTEM-001: API Endpoint Validation
**Priority**: MEDIUM | **Duration**: 3 minutes

**Test Steps**:
1. Verify key API endpoints are accessible:
   - Document creation: POST /api/v1/documents/
   - File upload: POST /api/v1/documents/files/{id}/upload
   - Document types: GET /api/v1/documents/types
   - Document categories: GET /api/v1/documents/categories
2. Check response codes and data

**Expected Results**:
- ✅ All endpoints return appropriate response codes
- ✅ Document creation API returns 200 with document data
- ✅ File upload API returns 200 with version information
- ✅ Types API returns 10+ document types
- ✅ Categories API returns 20+ categories

---

### TC-SYSTEM-002: Error Handling & Validation
**Priority**: MEDIUM | **Duration**: 4 minutes

**Test Steps**:
1. Test error scenarios:
   - Try to start review without uploaded file
   - Upload oversized file (if validation exists)
   - Submit form with missing required fields
2. Verify appropriate error messages

**Expected Results**:
- ✅ Review blocked when no file uploaded
- ✅ File size validation working (if implemented)
- ✅ Form validation prevents submission with missing data
- ✅ Error messages clear and helpful
- ✅ System remains stable during error conditions

---

## 🎯 **UAT SUCCESS CRITERIA**

### Pass/Fail Criteria
- **Critical Tests (HIGH Priority)**: 100% pass rate required
- **Important Tests (MEDIUM Priority)**: 100% pass rate required  
- **Overall Phase 2 Success**: All core workflow functionality operational

### Phase 2 Completion Definition
- ✅ Document creation with metadata (**Complete**)
- ✅ Mandatory file upload enforcement (**Complete**)
- ✅ File upload functionality with version tracking (**Complete**)
- ✅ Workflow progression after file upload (**Complete**)
- ✅ Status-based UI behavior (**Complete**)
- ✅ Review and approval workflows (**Complete**)

### Known Phase 2 Scope
- **IN SCOPE**: Document lifecycle, file upload, basic workflow
- **OUT OF SCOPE**: Advanced file processing, digital signatures (Phase 3)
- **OUT OF SCOPE**: Multiple file versions, advanced search (Phase 3)

---

## 📝 **UAT EXECUTION TRACKING**

### Test Execution Log
| Test Case | Priority | Status | Pass/Fail | Notes | Date |
|-----------|----------|--------|-----------|--------|------|
| TC-SETUP-001 | CRITICAL | PENDING | - | System access verification | - |
| TC-DOC-001 | HIGH | PENDING | - | Document creation testing | - |
| TC-UPLOAD-001 | HIGH | PENDING | - | Upload validation testing | - |
| TC-UPLOAD-002 | HIGH | PENDING | - | File upload functionality | - |
| TC-UPLOAD-003 | HIGH | PENDING | - | Workflow unlock verification | - |
| TC-WORKFLOW-001 | HIGH | PENDING | - | Review process initiation | - |
| TC-WORKFLOW-002 | MEDIUM | PENDING | - | Review execution | - |
| TC-SYSTEM-001 | MEDIUM | PENDING | - | API validation | - |
| TC-SYSTEM-002 | MEDIUM | PENDING | - | Error handling | - |

### Overall UAT Status
**Execution Progress**: 0/9 tests completed  
**Pass Rate**: TBD  
**Phase 2 Readiness**: Ready for UAT execution  
**Next Action**: Execute UAT test cases

---

## 🎉 **UAT COMPLETION SIGN-OFF**

### Business Acceptance Criteria
- [ ] All document creation workflows functional
- [ ] File upload requirement properly enforced  
- [ ] Document status progression working correctly
- [ ] User interface intuitive and professional
- [ ] System performance acceptable for business use

### Technical Acceptance Criteria  
- [ ] All Phase 2 APIs operational
- [ ] File upload and storage working correctly
- [ ] Database integration stable
- [ ] Error handling robust
- [ ] Security controls functioning

### UAT Sign-off
**Business Owner**: _________________ Date: _______  
**Technical Owner**: _________________ Date: _______  
**QA Lead**: _________________ Date: _______

**Final Status**: [ ] PHASE 2 ACCEPTED [ ] PHASE 2 NEEDS WORK [ ] PHASE 2 REJECTED

---

*This UAT plan validates EDMS Phase 2 completion with end-to-end document lifecycle testing including mandatory file upload requirements.*