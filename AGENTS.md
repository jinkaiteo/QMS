# QMS Platform - Developer Guide

## Project Overview

**QMS Pharmaceutical System v3.0** - A comprehensive Quality Management System for pharmaceutical manufacturing with integrated modules for document management (EDMS), laboratory information management (LIMS), training management (TMS), and quality/risk management (QRM).

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.104.1 with Python 3.8+
- **Database**: PostgreSQL 18 with SQLAlchemy 2.0.23 ORM
- **Cache**: Redis 7 for session management and caching
- **Storage**: MinIO for object storage (documents, files)
- **Search**: Elasticsearch 8.11.0 for full-text search
- **Authentication**: JWT with python-jose and passlib
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Testing**: pytest with async support

#### Frontend
- **Framework**: React 18.2.0 with TypeScript 5.2.2
- **Build Tool**: Vite 4.5.0 for fast development builds
- **UI Library**: Material-UI (MUI) 5.14.18 with emotion styling
- **State Management**: Redux Toolkit with React-Redux
- **Routing**: React Router DOM 6.20.1
- **Data Fetching**: React Query 3.39.3 with Axios
- **Forms**: React Hook Form with Yup validation
- **Charts**: Recharts for data visualization

#### Deployment
- **Containerization**: Docker/Podman with multi-stage builds
- **Orchestration**: Docker Compose for development and production
- **Reverse Proxy**: Nginx for load balancing and SSL termination
- **Monitoring**: Prometheus + Grafana for metrics and dashboards
- **CI/CD**: GitHub Actions for automated testing and deployment

## Project Structure

### Backend Architecture (`backend/`)
```
app/
├── main.py                 # FastAPI application entry point
├── api/v1/                 # API version 1 endpoints
│   ├── api.py             # Main API router configuration
│   └── endpoints/         # Individual module endpoints
├── core/                   # Core application configuration
│   ├── config.py          # Environment and app settings
│   ├── database.py        # Database connection and session management
│   ├── security.py        # Authentication and authorization
│   └── logging.py         # Structured logging configuration
├── models/                 # SQLAlchemy database models
├── schemas/               # Pydantic request/response schemas
└── services/              # Business logic and service layer
```

### Frontend Architecture (`frontend/`)
```
src/
├── App.tsx                # Main application component with routing
├── main.tsx              # React application entry point
├── components/           # Reusable UI components
│   ├── Common/          # Shared components (ErrorBoundary, Loading)
│   └── Layout/          # Layout components (Header, Sidebar)
├── pages/               # Page-level components for each module
├── services/            # API client services and HTTP utilities
├── store/               # Redux store configuration and slices
├── types/               # TypeScript type definitions
└── utils/               # Utility functions and helpers
```

### Database Structure (`database/`)
```
init/                    # Database initialization scripts (numbered order)
├── 01_create_extensions.sql
├── 02_create_core_tables.sql
├── 03_insert_default_data.sql
├── 04_create_edms_tables.sql
├── 05_insert_edms_data.sql
├── 06_create_qrm_tables.sql
├── 07_create_training_tables.sql
├── 08_insert_training_data.sql
├── 09_create_lims_tables.sql
└── 10_insert_lims_data.sql
```

### Deployment Structure (`deployment/`)
```
├── docker-compose.prod.yml    # Production container orchestration
├── Dockerfile.prod           # Production container build
├── .env.prod                # Production environment variables
├── nginx.conf               # Reverse proxy configuration
├── production/              # Production-specific configurations
│   ├── config/             # Service configurations
│   ├── scripts/            # Deployment and maintenance scripts
│   └── monitoring/         # Monitoring and alerting setup
└── ssl/                    # SSL certificates and configurations
```

## Core Modules

### 1. Authentication & User Management
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- User profile management with department assignments
- Password policies and security features
- **Endpoints**: `/api/v1/auth/*`, `/api/v1/users/*`

### 2. Electronic Document Management System (EDMS)
- Document lifecycle management (create, review, approve, retire)
- Version control with change tracking
- Digital signatures and approval workflows
- Document categories and metadata management
- **Endpoints**: `/api/v1/documents/*`

### 3. Training Management System (TMS)
- Training program creation and management
- Employee assignment and progress tracking
- Compliance monitoring and reporting
- Integration with EDMS for training materials
- **Endpoints**: `/api/v1/training/*`
- **Status**: Phase 1 Complete - Database integrated, API functional

### 4. Laboratory Information Management System (LIMS)
- Sample tracking and management
- Test method definitions and execution
- Instrument integration and calibration
- Results management and reporting
- **Endpoints**: `/api/v1/lims/*`

### 5. Quality Risk Management (QRM)
- Quality event management (deviations, complaints, audits)
- CAPA (Corrective and Preventive Action) workflows
- Risk assessment and mitigation tracking
- **Endpoints**: `/api/v1/quality-events/*`, `/api/v1/capas/*`

## Development Guidelines

### Backend Development

#### Database Models
- All models inherit from `BaseModel` in `app/models/base.py`
- Use soft deletes with `is_deleted` flag
- Include audit fields: `created_at`, `updated_at`, `version`
- Use UUID for external references and integer IDs for internal use

#### API Endpoints
- Follow RESTful conventions with proper HTTP methods
- Use Pydantic schemas for request/response validation
- Include proper error handling with meaningful HTTP status codes
- Add comprehensive docstrings for automatic API documentation
- Implement pagination for list endpoints

#### Database Schema Conventions
```sql
-- Table naming: plural snake_case
CREATE TABLE training_programs (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Foreign key naming: {referenced_table}_id
training_assignments (
    program_id INTEGER REFERENCES training_programs(id),
    employee_id INTEGER REFERENCES users(id)
);
```

#### Service Layer Pattern
```python
class TrainingService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def create_program(self, program_data: TrainingProgramCreate) -> TrainingProgram:
        # Business logic implementation
        # Validation, authorization, audit logging
        pass
```

### Frontend Development

#### Component Structure
- Use functional components with TypeScript
- Implement proper error boundaries for robust error handling
- Follow Material-UI design system and theming
- Use React Hook Form for form management with Yup validation

#### State Management
- Use Redux Toolkit for global state management
- Create feature-specific slices for each module
- Use React Query for server state management and caching
- Keep component-local state for UI-only concerns

#### Route Protection
```tsx
<ProtectedRoute>
  <Layout>
    <ModulePage />
  </Layout>
</ProtectedRoute>
```

#### API Service Pattern
```typescript
class TrainingService {
  private baseURL = '/api/v1/training'
  
  async getPrograms(): Promise<TrainingProgram[]> {
    const response = await apiClient.get(`${this.baseURL}/programs`)
    return response.data
  }
}
```

### Database Integration Guidelines

#### Training Management Integration
- Training tables are integrated with existing user and department structures
- Use foreign key references to `users(id)` for employee assignments
- Leverage existing `audit_logs` table for change tracking
- Follow the integrated schema in `database/training_schema_integrated.sql`

#### Migration Strategy
- Use numbered SQL files in `database/init/` for sequential execution
- Test migrations in development environment first
- Create rollback procedures for production deployments
- Document schema changes in commit messages

## Container Deployment

### Development Environment
```bash
# Start development stack
docker-compose -f docker-compose.dev.yml up -d

# Or with Podman
podman-compose -f podman-compose.dev.yml up -d
```

### Production Environment
```bash
# Navigate to deployment directory
cd deployment/

# Configure environment variables
cp .env.prod.template .env.prod
# Edit .env.prod with production values

# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d
```

### Container Health Checks
- All services include health check configurations
- Database: `pg_isready` check
- Redis: `ping` command check
- Application: HTTP health endpoint check
- MinIO: Health endpoint check

## Environment Configuration

### Required Environment Variables
```bash
# Database Configuration
POSTGRES_DB=qms_prod
POSTGRES_USER=qms_user
POSTGRES_PASSWORD=<secure_password>

# Application Security
SECRET_KEY=<random_secret_key>
JWT_SECRET_KEY=<jwt_secret>

# External Services
REDIS_PASSWORD=<redis_password>
MINIO_ROOT_USER=<minio_user>
MINIO_ROOT_PASSWORD=<minio_password>
```

### Frontend Environment Variables
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api

# Feature Flags
VITE_ENABLE_TRAINING=true
VITE_ENABLE_EDMS_INTEGRATION=true
```

## Testing Guidelines

### Backend Testing
- Use pytest with async support for API testing
- Include integration tests for database operations
- Mock external services (Redis, MinIO) in unit tests
- Test authentication and authorization scenarios
- Performance testing with Locust for load testing

### Frontend Testing
- Use React Testing Library for component testing
- Test user interactions and form submissions
- Mock API calls with MSW (Mock Service Worker)
- Include accessibility testing
- Visual regression testing for UI components

## Quality Assurance

### Code Quality Tools
- **Backend**: Black (formatting), isort (imports), flake8 (linting), mypy (type checking)
- **Frontend**: ESLint (linting), TypeScript compiler (type checking)
- **Pre-commit hooks**: Run quality checks before commits

### Security Considerations
- Input validation on all API endpoints
- SQL injection prevention with parameterized queries
- XSS protection with proper input sanitization
- CORS configuration for production environments
- Regular dependency updates for security patches

## Monitoring and Observability

### Application Monitoring
- Prometheus metrics collection
- Grafana dashboards for visualization
- Structured logging with correlation IDs
- Health check endpoints for all services

### Performance Monitoring
- Database query performance tracking
- API response time monitoring
- Frontend bundle size optimization
- Memory usage and resource monitoring

## Current Integration Status

### Training Management System (TMS)
- **Database Integration**: ✅ Complete - 6 training tables integrated with existing QMS schema
- **Backend API**: ✅ Available - Full CRUD operations with audit integration
- **Frontend UI**: ✅ Complete - Comprehensive training management interface
- **Mock API**: ✅ Functional - Development and testing support on port 3001
- **Production Backend**: ⚠️ Container deployment issues (environment configuration)

### Known Issues
- Backend container (`qms-app-prod`) failing with database connection issues
- Monitoring services (Prometheus/Grafana) not responding despite container health
- Frontend not currently running (easily resolvable)

### Recovery Procedures
- Complete Podman setup documented in `PODMAN_SETUP_MEMORY.md`
- Database integration preserved and functional
- Multiple deployment scripts available for different scenarios
- Mock API provides full functionality while production issues are resolved

## Best Practices

### Development Workflow
1. Create feature branches from `main`
2. Write tests before implementing features (TDD)
3. Use conventional commit messages
4. Submit pull requests with comprehensive descriptions
5. Ensure all CI checks pass before merging

### Database Operations
- Always use migrations for schema changes
- Test migrations with production-like data volumes
- Create database backups before major changes
- Use transactions for multi-table operations

### Security Best Practices
- Never commit secrets or credentials to version control
- Use environment variables for configuration
- Implement proper input validation and sanitization
- Follow principle of least privilege for database access
- Regular security audits and dependency updates

### Performance Optimization
- Use database indexes for frequently queried columns
- Implement caching strategies with Redis
- Optimize frontend bundle sizes with code splitting
- Monitor and profile application performance regularly

---

For specific module implementation details, refer to the comprehensive documentation files in the project root, particularly `QMS_Technical_Architecture.md` and module-specific implementation guides.