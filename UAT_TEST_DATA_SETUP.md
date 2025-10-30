# 🧪 UAT Test Data Setup Guide

**Purpose**: Prepare comprehensive test data for QMS Platform UAT  
**Status**: Ready for Execution  
**Environment**: Production-like UAT Environment

## 📊 Current Test Data Status

### ✅ Existing Test Data (Production Ready)
- **Users**: 3 active users with authentication
- **Training Programs**: 4 comprehensive programs
- **Document Types**: 5 pharmaceutical document types
- **Document Categories**: 5 business categories
- **Departments**: 9 organizational units
- **Audit Logs**: 15+ system activity entries

---

## 👥 **UAT USER ACCOUNTS**

### Administrative Users
| Username | Password | Role | Purpose | Status |
|----------|----------|------|---------|--------|
| admin | admin123 | System Admin | Full system access | ✅ Active |
| qmanager | admin123 | Quality Manager | Quality oversight | ✅ Active |
| testuser2 | TestPass123! | Standard User | Regular operations | ✅ Active |

### Recommended Additional UAT Users
```sql
-- Execute in production database for additional test users
INSERT INTO users (username, email, first_name, last_name, password_hash, status) VALUES
('uat_reviewer', 'reviewer@qms-test.com', 'UAT', 'Reviewer', '$2b$12$vVhZaCqzSwZy4cFTl5VdJ.iNNr.WJsNrb9xb0JNhFmBvdZR9/VYYq', 'active'),
('uat_approver', 'approver@qms-test.com', 'UAT', 'Approver', '$2b$12$vVhZaCqzSwZy4cFTl5VdJ.iNNr.WJsNrb9xb0JNhFmBvdZR9/VYYq', 'active'),
('uat_employee', 'employee@qms-test.com', 'UAT', 'Employee', '$2b$12$vVhZaCqzSwZy4cFTl5VdJ.iNNr.WJsNrb9xb0JNhFmBvdZR9/VYYq', 'active');
```
*Password for all UAT users: "password"*

---

## 📚 **TRAINING TEST DATA**

### Current Training Programs (Ready for Testing)
1. **GMP Training Program**
   - Type: Mandatory
   - Duration: 40 hours
   - Modules: 3 (Introduction, Documentation, Practical)
   - Status: Available for assignment

2. **Quality Control Procedures**
   - Type: Mandatory
   - Duration: 24 hours  
   - Modules: 2 (Testing Procedures, Lab Safety)
   - Status: Available for assignment

3. **Safety and Hazard Management**
   - Type: Mandatory
   - Duration: 16 hours
   - Status: Ready for modules

4. **Data Integrity Training**
   - Type: Mandatory
   - Duration: 32 hours
   - Modules: 2 (Fundamentals, ALCOA+ Principles)
   - Status: Active

### UAT Training Assignments
```sql
-- Create test assignments for UAT users
INSERT INTO training_assignments (program_id, employee_id, assigned_by, due_date, status, progress) VALUES
(7, 1, 1, NOW() + INTERVAL '30 days', 'assigned', 0),
(8, 1, 1, NOW() + INTERVAL '45 days', 'in_progress', 25),
(11, 1, 1, NOW() + INTERVAL '60 days', 'completed', 100);
```

---

## 📄 **DOCUMENT TEST DATA**

### Document Types (Production Ready)
| ID | Name | Code | Prefix | Status |
|----|------|------|--------|--------|
| 1 | Standard Operating Procedure | SOP | SOP | ✅ Active |
| 2 | Policy | POL | POL | ✅ Active |
| 3 | Work Instruction | WI | WI | ✅ Active |
| 4 | Form | FORM | FORM | ✅ Active |
| 5 | Manual | MAN | MAN | ✅ Active |

### Document Categories (Production Ready)
| ID | Name | Code | Color | Icon |
|----|------|------|-------|------|
| 1 | Quality Management | QM | #2E7D32 | quality_check |
| 2 | Manufacturing | MFG | #1976D2 | precision_manufacturing |
| 3 | Laboratory | LAB | #7B1FA2 | biotech |
| 4 | Regulatory | REG | #D32F2F | gavel |
| 5 | Training | TRAIN | #388E3C | school |

### Sample Documents for Upload Testing
**Recommended test files to prepare**:
1. **Sample_SOP.pdf** - Standard Operating Procedure example
2. **Quality_Policy.docx** - Company quality policy document  
3. **Training_Manual.pdf** - Training material example
4. **Work_Instruction.docx** - Detailed work instruction
5. **Compliance_Form.xlsx** - Regulatory compliance form

---

## 🏢 **ORGANIZATIONAL TEST DATA**

### Departments (Production Ready)
- Quality Assurance
- Manufacturing
- Laboratory
- Regulatory Affairs
- Human Resources
- Information Technology
- Research & Development
- Supply Chain
- Executive Management

### User-Department Assignments
```sql
-- Assign UAT users to departments for realistic testing
UPDATE users SET department_id = 1 WHERE username = 'uat_reviewer';   -- QA
UPDATE users SET department_id = 2 WHERE username = 'uat_approver';   -- Manufacturing  
UPDATE users SET department_id = 3 WHERE username = 'uat_employee';   -- Laboratory
```

---

## 🔍 **UAT TEST SCENARIOS DATA**

### Authentication Testing
- **Valid Credentials**: admin/admin123, qmanager/admin123
- **Invalid Credentials**: baduser/wrongpass
- **Edge Cases**: Empty fields, special characters

### Training Management Testing
- **Program Access**: 4 available programs
- **Assignment States**: Assigned, In Progress, Completed
- **Progress Tracking**: 0%, 25%, 100% completion scenarios

### Document Management Testing
- **Upload Tests**: Various file types (PDF, DOCX, XLSX)
- **Workflow Tests**: Review and approval scenarios
- **Version Control**: Multiple document versions

### System Administration Testing
- **User Management**: View user list, roles, permissions
- **Audit Logs**: System activity tracking
- **Health Monitoring**: Service status verification

---

## 📋 **UAT ENVIRONMENT SETUP CHECKLIST**

### Pre-UAT Verification
- [ ] All services operational (7 containers)
- [ ] Database accessible with test data
- [ ] Frontend serving on http://localhost:3002
- [ ] Backend API responding on http://localhost:8000
- [ ] Authentication working with test credentials

### Test Data Validation
- [ ] User accounts accessible
- [ ] Training programs visible
- [ ] Document types and categories loaded
- [ ] Organizational structure complete
- [ ] Audit logging functional

### UAT Infrastructure
- [ ] Test file repository prepared
- [ ] Browser compatibility verified
- [ ] Performance baseline established
- [ ] Test result tracking system ready

---

## 🎯 **UAT EXECUTION PREPARATION**

### Test Environment URLs
- **Frontend Application**: http://localhost:3002
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Test Credentials
- **Admin Access**: admin / admin123
- **Quality Manager**: qmanager / admin123  
- **Standard User**: testuser2 / TestPass123!

### Test Data Summary
- **Total Users**: 3+ (expandable to 6 for comprehensive testing)
- **Training Programs**: 4 with varied complexity
- **Document Framework**: 5 types × 5 categories = 25 combinations
- **Organizational Units**: 9 departments for role testing

---

## 📊 **SUCCESS METRICS**

### Data Integrity Validation
- All test data loads without errors
- User authentication successful across all accounts
- Training assignments properly linked
- Document categorization functional

### Functional Validation
- Core workflows operational with test data
- Cross-module data relationships maintained
- Audit trails capture test activities
- Performance acceptable with test load

**UAT Test Data Status**: ✅ **READY FOR UAT EXECUTION**

*Execute this setup before beginning formal UAT to ensure comprehensive test coverage with realistic pharmaceutical industry scenarios.*