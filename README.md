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

## Next Steps

Phase 2 will include:
- Complete EDMS module
- Document workflows
- Digital signature implementation
- Advanced search capabilities

## Support

For technical support or questions:
- Review the API documentation at `/docs`
- Check the audit logs for compliance issues
- Verify system health at `/api/v1/system/health`

## License

Proprietary - Pharmaceutical Quality Management System