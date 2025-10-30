# 📚 QMS Platform v3.0 - User Training Guide

## 🎯 **Welcome to QMS Platform v3.0**

Welcome to your comprehensive Quality Management System for pharmaceutical manufacturing. This guide will help you navigate and use all the key features of the QMS Platform effectively.

---

## 📋 **Table of Contents**

1. [Getting Started](#getting-started)
2. [System Overview](#system-overview)
3. [Login and Authentication](#login-and-authentication)
4. [Dashboard Navigation](#dashboard-navigation)
5. [User Management](#user-management)
6. [Training Management](#training-management)
7. [Document Management](#document-management)
8. [Quality Management](#quality-management)
9. [System Administration](#system-administration)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## 🚀 **Getting Started**

### **System Requirements**
- **Web Browser**: Chrome, Firefox, Safari, or Edge (latest versions)
- **Internet Connection**: Stable connection required
- **Screen Resolution**: Minimum 1024x768 (1920x1080 recommended)
- **User Account**: Valid QMS user credentials

### **Accessing the System**
1. Open your web browser
2. Navigate to: `http://your-qms-server:3002`
3. You'll see the QMS Platform login screen
4. Enter your credentials (provided by your system administrator)

### **First Time Login Checklist**
- [ ] Verify your user profile information
- [ ] Review your assigned roles and permissions
- [ ] Complete mandatory training assignments
- [ ] Set up notification preferences
- [ ] Review company policies and procedures

---

## 🔍 **System Overview**

### **QMS Platform Modules**

The QMS Platform consists of several integrated modules:

#### **🏠 Dashboard**
- System overview and key metrics
- Quick access to frequently used functions
- Notifications and alerts
- Personal task list

#### **👥 User Management**
- User profiles and contact information
- Role-based access control
- Department assignments
- User activity tracking

#### **🎓 Training Management System (TMS)**
- Training program catalog
- Course assignments and scheduling
- Progress tracking and reporting
- Compliance monitoring

#### **📄 Document Management (EDMS)**
- Document creation and editing
- Version control and approval workflows
- Document search and retrieval
- Regulatory compliance tracking

#### **⚖️ Quality Management (QRM)**
- Quality event reporting
- CAPA (Corrective and Preventive Actions)
- Audit management
- Risk assessment tools

#### **🔬 Laboratory Information Management (LIMS)**
- Sample tracking and management
- Test protocols and procedures
- Results recording and analysis
- Equipment calibration tracking

---

## 🔐 **Login and Authentication**

### **Standard Login Process**

1. **Navigate to Login Page**
   - Open your web browser
   - Go to the QMS Platform URL
   - Click "Login" if not automatically redirected

2. **Enter Credentials**
   ```
   Username: [Your assigned username]
   Password: [Your secure password]
   ```

3. **Two-Factor Authentication** (if enabled)
   - Enter the code from your authenticator app
   - Or use SMS verification code

4. **Dashboard Access**
   - Upon successful login, you'll see the main dashboard
   - Review any pending notifications or alerts

### **Password Security**

**Password Requirements:**
- Minimum 8 characters
- Include uppercase and lowercase letters
- Include at least one number
- Include at least one special character
- Cannot reuse last 5 passwords

**Password Best Practices:**
- Change passwords every 90 days
- Never share your password
- Use unique passwords for each system
- Consider using a password manager

### **Session Management**

- **Session Timeout**: 30 minutes of inactivity
- **Session Extension**: Click "Extend Session" when prompted
- **Secure Logout**: Always use the "Logout" button
- **Multiple Sessions**: Only one active session per user

---

## 🏠 **Dashboard Navigation**

### **Main Dashboard Layout**

```
┌─────────────────────────────────────────────────────┐
│ QMS Platform v3.0          [Notifications] [Profile]│
├─────────────────────────────────────────────────────┤
│ [Dashboard] [Training] [Documents] [Quality] [Admin]│
├─────────────────────────────────────────────────────┤
│                                                     │
│  📊 Key Metrics        📋 My Tasks                  │
│  ┌─────────────┐      ┌─────────────┐               │
│  │ Training:   │      │ • Complete  │               │
│  │ 85% Complete│      │   Safety    │               │
│  │             │      │   Training  │               │
│  │ Documents:  │      │ • Review    │               │
│  │ 12 Pending  │      │   SOP-001   │               │
│  └─────────────┘      └─────────────┘               │
│                                                     │
│  🔔 Recent Alerts     📈 System Status              │
│  ┌─────────────┐      ┌─────────────┐               │
│  │ • New CAPA  │      │ System:     │               │
│  │   #2024-001 │      │ ✅ Online   │               │
│  │ • Training  │      │ Database:   │               │
│  │   Due Soon  │      │ ✅ Healthy  │               │
│  └─────────────┘      └─────────────┘               │
└─────────────────────────────────────────────────────┘
```

### **Navigation Menu**

**Primary Navigation:**
- **Dashboard**: System overview and personal workspace
- **Training**: Training management and course access
- **Documents**: Document library and workflow management
- **Quality**: Quality events, CAPAs, and audits
- **Admin**: System administration (admin users only)

**Secondary Navigation:**
- **Notifications**: System alerts and messages
- **Profile**: Personal settings and preferences
- **Help**: User guides and support resources
- **Logout**: Secure session termination

### **Dashboard Widgets**

**Key Metrics Widget**
- Training completion percentage
- Pending document reviews
- Open quality events
- Overdue tasks

**My Tasks Widget**
- Personal task assignments
- Due dates and priorities
- Quick action buttons
- Progress indicators

**Recent Alerts Widget**
- System notifications
- Quality alerts
- Training reminders
- Document approvals

**System Status Widget**
- Application health
- Database connectivity
- Service availability
- Performance metrics

---

## 👥 **User Management**

### **User Profile Management**

#### **Viewing Your Profile**
1. Click on your name/avatar in the top right
2. Select "Profile" from the dropdown
3. Review your personal information

#### **Updating Profile Information**
1. Navigate to your profile page
2. Click "Edit Profile"
3. Update the following fields:
   - **Personal Information**: Name, email, phone
   - **Department**: Current department assignment
   - **Role**: Job title and responsibilities
   - **Emergency Contact**: Contact information
   - **Preferences**: Notification settings, language

4. Click "Save Changes"
5. Verify updates were applied correctly

#### **Profile Information Fields**

**Required Fields:**
- Full Name
- Email Address
- Department
- Job Title
- Employee ID

**Optional Fields:**
- Phone Number
- Office Location
- Manager
- Emergency Contact
- Profile Photo

### **Role and Permission Management**

#### **Understanding Roles**

**Standard User Roles:**
- **Employee**: Basic access to training and documents
- **Supervisor**: Team management and approval rights
- **Quality Manager**: Quality system oversight
- **Administrator**: Full system access and configuration

#### **Permission Categories**
- **Read**: View information and reports
- **Write**: Create and edit records
- **Approve**: Approve workflows and documents
- **Admin**: System configuration and user management

#### **Checking Your Permissions**
1. Go to Profile → Permissions
2. Review your assigned roles
3. View detailed permission matrix
4. Contact administrator for permission changes

### **Department Management**

#### **Department Structure**
- **Manufacturing**: Production operations
- **Quality Assurance**: Quality control and compliance
- **Quality Control**: Testing and analysis
- **Research & Development**: Product development
- **Regulatory Affairs**: Compliance and submissions
- **IT**: Information technology support

#### **Department-Specific Features**
Each department may have access to different modules and features based on their operational needs.

---

## 🎓 **Training Management**

### **Training Dashboard Overview**

The Training Management System (TMS) helps you:
- Track mandatory and optional training
- Schedule and complete courses
- Monitor compliance status
- Generate training reports

### **Accessing Training Modules**

#### **Navigation to Training**
1. Click "Training" in the main navigation
2. You'll see the training dashboard with:
   - **My Training**: Assigned courses and progress
   - **Available Courses**: Course catalog
   - **Completed Training**: Historical records
   - **Compliance Status**: Regulatory requirements

#### **Training Dashboard Layout**
```
┌─────────────────────────────────────────────────────┐
│ Training Management                                 │
├─────────────────────────────────────────────────────┤
│ 📊 Progress Overview                                │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│ │ Completed   │ │ In Progress │ │ Overdue     │     │
│ │     15      │ │      3      │ │      1      │     │
│ └─────────────┘ └─────────────┘ └─────────────┘     │
│                                                     │
│ 📋 My Assigned Training                             │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Course Name        │ Due Date   │ Status        │ │
│ │ GMP Basics         │ 2024-02-15 │ In Progress   │ │
│ │ Safety Training    │ 2024-02-20 │ Not Started   │ │
│ │ Equipment Cleaning │ 2024-02-25 │ ⚠️ Overdue    │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### **Taking Training Courses**

#### **Starting a Course**
1. Navigate to Training → My Training
2. Find the course you want to take
3. Click "Start Course" or "Continue"
4. Review course objectives and requirements

#### **Course Structure**
Most courses include:
- **Introduction**: Course overview and objectives
- **Modules**: Learning content (videos, documents, presentations)
- **Knowledge Checks**: Quizzes and assessments
- **Final Assessment**: Completion test
- **Certification**: Course completion certificate

#### **Completing Course Modules**
1. **Read/Watch Content**: Complete each module thoroughly
2. **Take Notes**: Use the built-in note-taking feature
3. **Complete Activities**: Participate in interactive elements
4. **Pass Knowledge Checks**: Achieve minimum passing scores
5. **Final Assessment**: Complete the final exam

#### **Assessment Guidelines**
- **Passing Score**: Typically 80% or higher
- **Attempts**: Usually 3 attempts allowed
- **Time Limits**: Some assessments are timed
- **Resources**: Reference materials may be available

### **Training Records and Compliance**

#### **Viewing Training History**
1. Go to Training → Completed Training
2. View chronological list of completed courses
3. Download certificates and transcripts
4. Review compliance status

#### **Compliance Tracking**
- **Mandatory Training**: Required by regulations or company policy
- **Refresher Training**: Periodic recertification requirements
- **Job-Specific Training**: Role-based training requirements
- **Continuing Education**: Ongoing professional development

#### **Training Certificates**
- **Digital Certificates**: Automatically generated upon completion
- **PDF Downloads**: Available for printing and record-keeping
- **Verification**: Certificates include verification codes
- **Expiration**: Some certificates require periodic renewal

### **Training Administration** (Supervisors/Administrators)

#### **Assigning Training**
1. Navigate to Training → Manage Assignments
2. Select users or groups
3. Choose courses from catalog
4. Set due dates and priorities
5. Send notifications to assignees

#### **Monitoring Progress**
- **Individual Progress**: Track specific user progress
- **Team Reports**: Department-wide compliance status
- **Overdue Reports**: Identify training gaps
- **Completion Reports**: Generate compliance documentation

---

## 📄 **Document Management**

### **Document Management Overview**

The Electronic Document Management System (EDMS) provides:
- **Document Creation**: Create and edit documents online
- **Version Control**: Track document revisions and changes
- **Approval Workflows**: Route documents for review and approval
- **Search and Retrieval**: Find documents quickly and efficiently
- **Compliance Tracking**: Ensure regulatory compliance

### **Document Types**

#### **Standard Operating Procedures (SOPs)**
- Step-by-step process instructions
- Regulatory compliance procedures
- Safety and quality protocols
- Equipment operation procedures

#### **Work Instructions**
- Detailed task instructions
- Job aids and checklists
- Reference materials
- Training materials

#### **Forms and Templates**
- Data collection forms
- Report templates
- Quality forms
- Audit checklists

#### **Policies and Procedures**
- Company policies
- Regulatory procedures
- Quality manuals
- Safety procedures

### **Creating Documents**

#### **Document Creation Process**
1. Navigate to Documents → Create New
2. Select document type from template
3. Choose appropriate template
4. Fill in document metadata:
   - **Title**: Descriptive document title
   - **Document ID**: Unique identifier
   - **Department**: Owning department
   - **Category**: Document classification
   - **Author**: Document creator
   - **Review Date**: Scheduled review date

5. Create document content
6. Save as draft or submit for review

#### **Document Editor Features**
- **Rich Text Editing**: Formatting tools and styles
- **Table Support**: Create and edit tables
- **Image Insertion**: Add diagrams and images
- **Collaboration**: Multi-user editing capabilities
- **Comments**: Add review comments and suggestions
- **Track Changes**: Monitor document modifications

### **Document Workflow**

#### **Standard Approval Workflow**
```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Author    │──▶│   Review    │──▶│   Approve   │──▶│  Published  │
│   Creates   │   │  Technical  │   │   Quality   │   │   Active    │
│  Document   │   │   Review    │   │  Approval   │   │  Document   │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

#### **Workflow Steps**
1. **Draft**: Author creates document
2. **Technical Review**: Subject matter expert review
3. **Quality Review**: Quality department review
4. **Management Approval**: Final approval
5. **Publication**: Document becomes active
6. **Distribution**: Notify affected users

#### **Workflow Actions**
- **Submit for Review**: Move to next workflow step
- **Approve**: Accept document and move forward
- **Request Changes**: Return with comments for revision
- **Reject**: Decline document with explanation
- **Recall**: Author withdraws document from workflow

### **Document Search and Retrieval**

#### **Search Methods**
1. **Quick Search**: Search box in header
2. **Advanced Search**: Detailed search criteria
3. **Browse by Category**: Navigate document folders
4. **Filter Results**: Refine search results

#### **Search Criteria**
- **Document Title**: Full or partial title
- **Document ID**: Exact document number
- **Author**: Document creator
- **Department**: Owning department
- **Keywords**: Content keywords
- **Date Range**: Creation or modification dates
- **Status**: Draft, active, archived

#### **Search Results**
- **Document Preview**: Quick content preview
- **Metadata**: Document properties
- **Version History**: Previous versions
- **Related Documents**: Cross-references
- **Actions**: Open, download, share options

### **Version Control**

#### **Version Management**
- **Major Versions**: Significant content changes (1.0, 2.0, 3.0)
- **Minor Versions**: Editorial changes (1.1, 1.2, 1.3)
- **Version Comments**: Description of changes made
- **Version Comparison**: Side-by-side comparison tool

#### **Document Revision Process**
1. **Check Out**: Lock document for editing
2. **Edit Content**: Make necessary changes
3. **Save Changes**: Save new version
4. **Add Comments**: Describe what changed
5. **Check In**: Release document lock
6. **Submit**: Route through approval workflow

---

## ⚖️ **Quality Management**

### **Quality Management Overview**

The Quality Risk Management (QRM) module helps you:
- **Report Quality Events**: Document quality issues and deviations
- **Manage CAPAs**: Corrective and Preventive Actions
- **Conduct Audits**: Internal and external audit management
- **Risk Assessment**: Identify and mitigate quality risks

### **Quality Events**

#### **Types of Quality Events**
- **Deviations**: Departures from approved procedures
- **Non-Conformances**: Products not meeting specifications
- **Customer Complaints**: External quality concerns
- **OOS/OOT**: Out of Specification/Out of Trend results
- **Equipment Failures**: Manufacturing equipment issues

#### **Reporting Quality Events**
1. Navigate to Quality → Report Event
2. Select event type
3. Fill in event details:
   - **Event Date**: When the event occurred
   - **Location**: Where the event happened
   - **Description**: Detailed event description
   - **Product Impact**: Affected products or batches
   - **Severity**: High, Medium, Low classification
   - **Immediate Actions**: Actions taken immediately

4. Attach supporting documentation
5. Submit for investigation

#### **Quality Event Investigation**
1. **Initial Assessment**: Preliminary investigation
2. **Root Cause Analysis**: Detailed investigation
3. **Impact Assessment**: Determine product/process impact
4. **CAPA Development**: Create corrective actions
5. **Review and Approval**: Management review
6. **Closure**: Complete investigation

### **CAPA Management**

#### **CAPA Process Overview**
CAPA (Corrective and Preventive Action) addresses:
- **Corrective Actions**: Fix identified problems
- **Preventive Actions**: Prevent potential problems
- **Root Cause**: Address underlying causes
- **Effectiveness**: Verify actions work

#### **Creating a CAPA**
1. Navigate to Quality → CAPA → New CAPA
2. Link to originating quality event
3. Define CAPA details:
   - **CAPA Type**: Corrective or Preventive
   - **Root Cause**: Identified root cause
   - **Actions Required**: Specific actions to take
   - **Responsible Person**: Who will execute
   - **Target Date**: When to complete
   - **Success Criteria**: How to measure effectiveness

4. Submit for approval

#### **CAPA Implementation**
1. **Action Planning**: Develop detailed action plan
2. **Resource Allocation**: Assign necessary resources
3. **Implementation**: Execute planned actions
4. **Documentation**: Record all activities
5. **Verification**: Confirm actions completed
6. **Effectiveness Check**: Verify problem resolution

### **Audit Management**

#### **Audit Types**
- **Internal Audits**: Self-assessment audits
- **External Audits**: Regulatory or customer audits
- **Supplier Audits**: Vendor qualification audits
- **System Audits**: Quality system assessments

#### **Audit Process**
1. **Audit Planning**: Schedule and prepare
2. **Audit Execution**: Conduct audit activities
3. **Finding Documentation**: Record observations
4. **Report Generation**: Create audit report
5. **CAPA Assignment**: Address findings
6. **Follow-up**: Verify corrective actions

---

## 🔬 **Laboratory Information Management**

### **LIMS Overview**

The Laboratory Information Management System (LIMS) provides:
- **Sample Management**: Track samples throughout testing
- **Test Management**: Manage test methods and protocols
- **Results Management**: Record and approve test results
- **Equipment Management**: Track equipment and calibrations

### **Sample Management**

#### **Sample Registration**
1. Navigate to LIMS → Samples → Register New
2. Enter sample information:
   - **Sample ID**: Unique sample identifier
   - **Sample Type**: Raw material, finished product, etc.
   - **Batch/Lot**: Associated batch information
   - **Collection Date**: When sample was collected
   - **Collector**: Who collected the sample
   - **Tests Required**: Which tests to perform

3. Generate sample labels
4. Submit for testing

#### **Sample Tracking**
- **Chain of Custody**: Track sample handling
- **Location**: Current sample location
- **Status**: Testing progress
- **Results**: Test outcomes
- **Disposition**: Final sample disposition

### **Test Management**

#### **Test Methods**
- **Standard Methods**: Approved test procedures
- **Custom Methods**: Company-specific tests
- **Method Validation**: Verification of test accuracy
- **Method Transfer**: Moving methods between labs

#### **Executing Tests**
1. Navigate to LIMS → Testing → My Assignments
2. Select sample to test
3. Review test method
4. Record test conditions
5. Enter test results
6. Review and submit results

---

## 🔧 **System Administration**

### **Administrative Functions** (Admin Users Only)

#### **User Administration**
- **User Creation**: Add new users to system
- **Role Assignment**: Assign user roles and permissions
- **Password Reset**: Help users with password issues
- **Account Deactivation**: Remove user access

#### **System Configuration**
- **Workflow Configuration**: Set up approval workflows
- **Notification Settings**: Configure system notifications
- **Integration Settings**: Connect external systems
- **Backup and Recovery**: System maintenance tasks

#### **Reporting and Analytics**
- **User Activity Reports**: Monitor system usage
- **Compliance Reports**: Regulatory compliance status
- **Performance Metrics**: System performance data
- **Audit Logs**: Complete system audit trail

---

## 🛠️ **Troubleshooting**

### **Common Issues and Solutions**

#### **Login Problems**
**Issue**: Cannot log in to the system
**Solutions**:
1. Verify username and password
2. Check for CAPS LOCK
3. Clear browser cache and cookies
4. Try a different browser
5. Contact IT support for password reset

#### **Performance Issues**
**Issue**: System running slowly
**Solutions**:
1. Check internet connection speed
2. Close unnecessary browser tabs
3. Clear browser cache
4. Disable browser extensions
5. Use a supported browser

#### **Document Access Issues**
**Issue**: Cannot open or edit documents
**Solutions**:
1. Check document permissions
2. Verify browser settings
3. Clear browser cache
4. Try downloading document
5. Contact document owner

#### **Training Issues**
**Issue**: Cannot complete training courses
**Solutions**:
1. Check course prerequisites
2. Verify browser compatibility
3. Disable pop-up blockers
4. Try a different browser
5. Contact training administrator

### **Getting Help**

#### **Help Resources**
- **Online Help**: Built-in help system
- **User Manual**: Detailed user documentation
- **Video Tutorials**: Step-by-step video guides
- **FAQ**: Frequently asked questions
- **Support Ticket**: Submit help requests

#### **Contact Information**
- **IT Help Desk**: [Your IT contact information]
- **Training Support**: [Training department contact]
- **Quality Support**: [Quality department contact]
- **System Administrator**: [Admin contact information]

---

## ✅ **Best Practices**

### **Security Best Practices**

#### **Password Security**
- Use strong, unique passwords
- Enable two-factor authentication
- Change passwords regularly
- Never share login credentials
- Log out when finished

#### **Data Protection**
- Classify data appropriately
- Follow data handling procedures
- Report security incidents immediately
- Use approved devices only
- Keep software updated

### **Document Management Best Practices**

#### **Document Creation**
- Use approved templates
- Follow naming conventions
- Include required metadata
- Review before submission
- Keep documents current

#### **Document Control**
- Check for latest version
- Follow change control procedures
- Maintain document history
- Archive obsolete documents
- Protect controlled documents

### **Quality Management Best Practices**

#### **Quality Event Reporting**
- Report events promptly
- Provide complete information
- Include supporting evidence
- Follow investigation procedures
- Implement corrective actions

#### **CAPA Management**
- Address root causes
- Set realistic timelines
- Assign clear responsibilities
- Monitor implementation
- Verify effectiveness

### **Training Best Practices**

#### **Course Completion**
- Complete training on time
- Read all materials thoroughly
- Take notes during training
- Ask questions when unclear
- Apply learning on the job

#### **Compliance Management**
- Track training requirements
- Complete refresher training
- Maintain training records
- Report training issues
- Participate in assessments

---

## 📞 **Support and Resources**

### **Quick Reference Card**

#### **Login Information**
- **URL**: [Your QMS URL]
- **Username**: [Your assigned username]
- **Password**: [Your secure password]

#### **Key Contacts**
- **IT Support**: [Phone/Email]
- **Training**: [Phone/Email]
- **Quality**: [Phone/Email]
- **Administration**: [Phone/Email]

#### **Important Links**
- **System Status**: [Status page URL]
- **Training Calendar**: [Calendar URL]
- **Policy Library**: [Policy URL]
- **Help Desk**: [Support URL]

### **Glossary of Terms**

**API**: Application Programming Interface
**CAPA**: Corrective and Preventive Action
**CFR**: Code of Federal Regulations
**EDMS**: Electronic Document Management System
**GMP**: Good Manufacturing Practice
**LIMS**: Laboratory Information Management System
**OOS**: Out of Specification
**OOT**: Out of Trend
**QRM**: Quality Risk Management
**SOP**: Standard Operating Procedure
**TMS**: Training Management System
**UAT**: User Acceptance Testing

---

## 📋 **Training Completion Checklist**

### **Basic System Navigation**
- [ ] Successfully log in to the system
- [ ] Navigate main dashboard
- [ ] Access all assigned modules
- [ ] Update personal profile
- [ ] Configure notification preferences

### **Training Management**
- [ ] View assigned training courses
- [ ] Complete a training module
- [ ] Take and pass an assessment
- [ ] Download a training certificate
- [ ] Check compliance status

### **Document Management**
- [ ] Search for a document
- [ ] Open and review a document
- [ ] Understand version control
- [ ] Follow a document workflow
- [ ] Create a new document (if authorized)

### **Quality Management**
- [ ] Report a quality event
- [ ] Review a CAPA assignment
- [ ] Understand investigation process
- [ ] Access audit information
- [ ] Complete quality forms

### **System Administration** (Admin Users)
- [ ] Add a new user
- [ ] Assign user roles
- [ ] Configure system settings
- [ ] Generate reports
- [ ] Monitor system health

---

**Training Guide Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Review Date]  
**Document ID**: QMS-TRG-001  
**Approved By**: [Quality Manager]

---

*This training guide is a controlled document. Ensure you are using the latest version available in the QMS document management system.*