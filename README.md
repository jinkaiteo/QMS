# QMS Pharmaceutical System

A 21 CFR Part 11 compliant Quality Management System for pharmaceutical organizations.

## Phase 1: Foundation Setup

This is the Phase 1 implementation focusing on:
- Core infrastructure setup
- User authentication and authorization
- Audit trail foundation
- Basic API structure

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd qms-system
   ```

2. **Start development environment**
   ```bash
   chmod +x scripts/start_development.sh
   ./scripts/start_development.sh
   ```

3. **Start the API server**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/v1/docs
   - Database Admin: http://localhost:5050
   - MinIO Console: http://localhost:9001

### Default Users

The system comes with pre-configured users:

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| sysadmin | Admin123! | System Administrator | Full system access |
| qmanager | Admin123! | Quality Manager | Quality operations |
| jdoe | Admin123! | Document Author | Create/edit documents |

## Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL 18
- **Cache**: Redis
- **Search**: Elasticsearch
- **Storage**: MinIO (S3-compatible)
- **Containers**: Podman/Docker

### Key Features
- 21 CFR Part 11 compliant electronic records
- Digital signatures with PKI
- Comprehensive audit trail
- Role-based access control
- Microsoft Entra ID integration
- Automated compliance reporting

## Development

### Project Structure
```
qms-system/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   └── requirements.txt
├── database/
│   └── init/            # Database initialization
├── docker-compose.dev.yml
└── scripts/
    └── start_development.sh
```

### API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh token

#### Users
- `GET /api/v1/users/` - List users
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user

#### System
- `GET /api/v1/system/health` - Health check
- `GET /api/v1/system/info` - System information

## Compliance

### 21 CFR Part 11 Requirements
- ✅ Electronic records with digital signatures
- ✅ User authentication and authorization
- ✅ Audit trail for all activities
- ✅ Data integrity controls
- ✅ System access controls

### ALCOA Principles
- **Attributable**: All actions linked to authenticated users
- **Legible**: Clear, readable data formats
- **Contemporaneous**: Real-time data capture
- **Original**: Source data preservation
- **Accurate**: Data validation and verification

## Security

### Authentication
- JWT-based authentication
- Password complexity requirements
- Account lockout protection
- Session management

### Authorization
- Role-based access control (RBAC)
- Granular permissions
- Module-specific roles

### Data Protection
- Encryption at rest and in transit
- Digital signatures for documents
- Audit trail integrity verification

## QMS Platform Status: **COMPLETE** 🎉

**🏆 MAJOR MILESTONE: Complete Quality Management System Platform**

All three foundational phases have been successfully implemented:

## Phase 1: Foundation ✅ 
**User Management, Authentication, and System Core**

## Phase 2: EDMS Module ✅
**Electronic Document Management System**

Phase 2 has been completed and includes:
- ✅ Complete EDMS (Electronic Document Management System) module
- ✅ Document types and categories management
- ✅ Document upload, versioning, and metadata management
- ✅ Document review and approval workflows
- ✅ Digital signature framework
- ✅ Advanced document search and filtering
- ✅ Document permissions and access control
- ✅ Full audit trail for document operations

### EDMS Features

#### Document Management
- **Document Types**: SOPs, Policies, Work Instructions, Forms, Manuals, Reports, etc.
- **Categories**: Hierarchical categorization (Quality, Manufacturing, Laboratory, etc.)
- **Version Control**: Complete version history with major/minor versioning
- **File Storage**: Secure file storage with integrity verification (SHA-256)
- **Metadata**: Keywords, tags, confidentiality levels, retention periods

#### Workflow Engine
- **Review Workflows**: Multi-step document review processes
- **Approval Workflows**: Document approval with digital signatures
- **Workflow Templates**: Predefined workflows for different document types
- **Due Dates & Notifications**: Workflow tracking with automated reminders

#### Digital Signatures
- **Electronic Signatures**: PKI-based digital signatures for document approval
- **Signature Types**: Author, Reviewer, Approver, Witness signatures
- **Non-repudiation**: Cryptographic proof of document authenticity
- **Audit Trail**: Complete signature history and verification

#### Search & Discovery
- **Full-text Search**: Search across document titles, descriptions, and content
- **Advanced Filters**: Filter by type, category, status, author, dates
- **Metadata Search**: Search by keywords, tags, and custom attributes
- **Permission-based Results**: Results filtered by user access rights

### API Endpoints

#### Document Management
- `GET /api/v1/documents/` - List documents with filters
- `POST /api/v1/documents/search` - Advanced document search
- `GET /api/v1/documents/{id}` - Get specific document
- `POST /api/v1/documents/upload` - Upload new document
- `PUT /api/v1/documents/{id}` - Update document metadata
- `GET /api/v1/documents/{id}/download` - Download document file
- `DELETE /api/v1/documents/{id}` - Delete document

#### Workflow Management
- `POST /api/v1/documents/{id}/start-review` - Start document review
- `POST /api/v1/documents/workflows/{id}/complete-review` - Complete review
- `POST /api/v1/documents/{id}/approve` - Approve document

#### Configuration
- `GET /api/v1/documents/types` - List document types
- `POST /api/v1/documents/types` - Create document type
- `GET /api/v1/documents/categories` - List document categories
- `POST /api/v1/documents/categories` - Create document category

### Database Schema

Phase 2 adds comprehensive EDMS tables:
- `document_types` - Document type definitions
- `document_categories` - Hierarchical categorization
- `documents` - Main document registry
- `document_versions` - Version history and file storage
- `document_workflows` - Review/approval workflows
- `workflow_steps` - Individual workflow steps
- `digital_signatures` - Electronic signatures
- `document_relationships` - Document dependencies
- `document_permissions` - Access control
- `document_comments` - Review comments and annotations

### Testing Phase 2

Run the Phase 2 test script:
```bash
python test_phase2_complete.py
```

## Phase 3: QRM Module ✅
**Quality Risk Management System**

Phase 3 has been completed and includes:
- ✅ Complete QRM (Quality Risk Management) module
- ✅ Quality event management with investigation workflows
- ✅ CAPA (Corrective and Preventive Actions) system
- ✅ Investigation assignment and tracking
- ✅ Root cause analysis framework
- ✅ Approval workflows and effectiveness verification
- ✅ Analytics and reporting dashboards
- ✅ Seamless integration with EDMS documents

### QRM Features

#### Quality Event Management
- **Event Types**: Configurable event classifications with severity levels
- **Incident Reporting**: Comprehensive event capture with impact assessment
- **Investigation Workflows**: Structured investigation processes with assignable investigators
- **Status Tracking**: Complete lifecycle from open to closure
- **Impact Assessment**: Patient safety, product quality, and regulatory impact evaluation

#### CAPA System
- **Action Planning**: Detailed corrective and preventive action management
- **Task Breakdown**: Individual action items with assignments and due dates
- **Resource Allocation**: Cost estimation and resource tracking
- **Approval Workflows**: Multi-level approval processes
- **Effectiveness Verification**: Systematic verification of action effectiveness
- **Progress Tracking**: Real-time completion percentage monitoring

#### Integration & Compliance
- **EDMS Integration**: Direct links to investigation documents and evidence
- **Audit Trail**: Complete compliance logging for 21 CFR Part 11
- **Role-based Access**: Permission-based access control
- **Analytics**: Real-time quality metrics and KPI dashboards

### API Endpoints (QRM)

#### Quality Event Management
- `GET /api/v1/quality-events/` - List quality events with filters
- `POST /api/v1/quality-events/search` - Advanced quality event search
- `GET /api/v1/quality-events/{id}` - Get specific quality event
- `POST /api/v1/quality-events/` - Create quality event
- `PUT /api/v1/quality-events/{id}` - Update quality event
- `POST /api/v1/quality-events/{id}/assign-investigator` - Assign investigator
- `POST /api/v1/quality-events/{id}/update-status` - Update event status

#### CAPA Management
- `GET /api/v1/capas/` - List CAPAs with filters
- `POST /api/v1/capas/search` - Advanced CAPA search
- `GET /api/v1/capas/{id}` - Get specific CAPA
- `POST /api/v1/capas/` - Create CAPA
- `PUT /api/v1/capas/{id}` - Update CAPA
- `POST /api/v1/capas/{id}/approve` - Approve CAPA
- `POST /api/v1/capas/{id}/verify-effectiveness` - Verify effectiveness
- `GET /api/v1/capas/{id}/actions` - Get CAPA actions
- `POST /api/v1/capas/{id}/actions` - Create CAPA action

#### Analytics & Reporting
- `GET /api/v1/quality-events/analytics/summary` - Quality events dashboard
- `GET /api/v1/capas/analytics/summary` - CAPA metrics dashboard

### Database Schema (QRM)

Phase 3 adds comprehensive QRM tables:
- `quality_event_types` - Event type definitions and classifications
- `quality_events` - Main quality events registry
- `quality_investigations` - Formal investigation records
- `capas` - Corrective and preventive actions
- `capa_actions` - Individual CAPA task breakdown
- `change_control_requests` - Change management framework
- `risk_assessments` - Risk assessment and management

### Testing Phase 3

Run the Phase 3 test script:
```bash
python test_phase3_qrm.py
```

## Next Steps - Phase 4 Options

**Phase 4 Development Options:**
- **TRM (Training Management)** - Competency tracking and training records
- **LIMS Foundation** - Laboratory information management integration
- **Advanced Analytics** - Enhanced reporting and trend analysis
- **Mobile Applications** - iOS/Android apps for field operations
- **API Integrations** - Third-party system integrations

## Support

For technical support or questions:
- Review the API documentation at `/docs`
- Check the audit logs for compliance issues
- Verify system health at `/api/v1/system/health`

## License

Proprietary - Pharmaceutical Quality Management System# Trigger new pipeline run
