# QMS System - Technical Architecture Deep Dive

## Table of Contents
1. [System Overview](#system-overview)
2. [Infrastructure Architecture](#infrastructure-architecture)
3. [Application Architecture](#application-architecture)
4. [Security Architecture](#security-architecture)
5. [Data Architecture](#data-architecture)
6. [Integration Architecture](#integration-architecture)
7. [Deployment Architecture](#deployment-architecture)

## System Overview

### Technology Stack
```
Frontend Layer:
├── React 18.2+ with TypeScript
├── Material-UI v5 (MUI)
├── Redux Toolkit for state management
├── React Query for API state management
├── React Hook Form for form handling
├── Chart.js for data visualization
└── PDF.js for document viewing

API Gateway:
├── FastAPI 0.104+ (Python 3.11+)
├── Uvicorn ASGI server
├── Pydantic for data validation
├── SQLAlchemy 2.0+ ORM
└── Alembic for database migrations

Backend Services:
├── Celery for async task processing
├── Redis for caching and message broker
├── Minio for object storage (S3 compatible)
├── OpenSSL for digital signatures
└── ReportLab for PDF generation

Database Layer:
├── PostgreSQL 18 (primary database)
├── Redis (cache and session store)
└── Elasticsearch (full-text search)

Infrastructure:
├── Podman containers (rootless)
├── Nginx reverse proxy
├── HAProxy load balancer
├── Prometheus monitoring
└── Grafana dashboards
```

### Microservices Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React)                  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│               API Gateway (FastAPI)                 │
├─────────────────┬───────────────────────────────────┤
│                 │                                   │
│  ┌──────────────▼──────────────┐ ┌─────────────────┐│
│  │      Service Layer          │ │  Business Logic ││
│  │  ┌─────────────────────────┐│ │  ┌─────────────┐││
│  │  │ User Management Service ││ │  │ EDMS Module │││
│  │  │ Audit Trail Service     ││ │  │ QRM Module  │││
│  │  │ Scheduler Service       ││ │  │ TRM Module  │││
│  │  │ Notification Service    ││ │  │ LIMS Module │││
│  │  │ Document Service        ││ │  └─────────────┘││
│  │  │ Workflow Engine         ││ │                 ││
│  │  └─────────────────────────┘│ └─────────────────┘│
│  └─────────────────────────────┘                   │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              Data Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐│
│  │ PostgreSQL  │ │    Redis    │ │  Elasticsearch  ││
│  │  (Primary)  │ │   (Cache)   │ │    (Search)     ││
│  └─────────────┘ └─────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────┘
```

## Infrastructure Architecture

### Container Architecture

```yaml
# docker-compose.yml structure
version: '3.8'
services:
  # Frontend
  qms-frontend:
    image: qms/frontend:latest
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=https://api.qms.local
      - REACT_APP_ENV=production
    networks:
      - qms-network

  # API Gateway
  qms-api:
    image: qms/api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://qms:password@db:5432/qms
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET}
    depends_on:
      - qms-db
      - qms-redis
    networks:
      - qms-network

  # Background Workers
  qms-worker:
    image: qms/api:latest
    command: celery worker -A app.celery -l info
    environment:
      - DATABASE_URL=postgresql://qms:password@db:5432/qms
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - qms-db
      - qms-redis
    networks:
      - qms-network

  # Scheduler
  qms-scheduler:
    image: qms/api:latest
    command: celery beat -A app.celery -l info
    environment:
      - DATABASE_URL=postgresql://qms:password@db:5432/qms
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - qms-db
      - qms-redis
    networks:
      - qms-network

  # Database
  qms-db:
    image: postgres:18
    environment:
      - POSTGRES_DB=qms
      - POSTGRES_USER=qms
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - qms-network

  # Cache & Message Broker
  qms-redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - qms-network

  # Object Storage
  qms-minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_PASSWORD}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - qms-network

  # Search Engine
  qms-elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - qms-network

  # Load Balancer
  qms-nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - qms-frontend
      - qms-api
    networks:
      - qms-network

volumes:
  postgres_data:
  redis_data:
  minio_data:
  elasticsearch_data:

networks:
  qms-network:
    driver: bridge
```

### High Availability Setup

```
┌─────────────────────────────────────────────────────┐
│                Load Balancer Layer                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐│
│  │   HAProxy   │ │    Nginx    │ │ SSL Termination ││
│  │  (Primary)  │ │ (Secondary) │ │   (Let's Encrypt)││
│  └─────────────┘ └─────────────┘ └─────────────────┘│
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│               Application Layer                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐│
│  │   Node 1    │ │   Node 2    │ │     Node 3      ││
│  │ (Frontend)  │ │   (API)     │ │   (Workers)     ││
│  └─────────────┘ └─────────────┘ └─────────────────┘│
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                Data Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐│
│  │ PostgreSQL  │ │ Redis       │ │  Elasticsearch  ││
│  │ (Primary)   │ │ (Cluster)   │ │   (Cluster)     ││
│  │ + Replica   │ │             │ │                 ││
│  └─────────────┘ └─────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────┘
```

## Application Architecture

### API Design Patterns

#### RESTful API Structure
```
/api/v1/
├── auth/
│   ├── login              POST
│   ├── logout             POST
│   ├── refresh            POST
│   └── profile            GET, PUT
├── users/
│   ├── /                  GET, POST
│   ├── /{id}              GET, PUT, DELETE
│   ├── /{id}/roles        GET, POST
│   └── /{id}/permissions  GET
├── edms/
│   ├── documents/         GET, POST
│   ├── documents/{id}     GET, PUT, DELETE
│   ├── documents/{id}/versions  GET, POST
│   ├── documents/{id}/workflow  POST
│   ├── documents/{id}/download  GET
│   └── documents/{id}/sign      POST
├── qrm/
│   ├── events/            GET, POST
│   ├── events/{id}        GET, PUT
│   ├── deviations/        GET, POST
│   ├── investigations/    GET, POST
│   ├── capas/             GET, POST
│   └── change-controls/   GET, POST
├── trm/
│   ├── curricula/         GET, POST
│   ├── syllabi/           GET, POST
│   ├── training-records/  GET, POST
│   └── assignments/       GET, POST
├── lims/
│   ├── samples/           GET, POST
│   ├── assays/            GET, POST
│   ├── equipment/         GET, POST
│   ├── inventory/         GET, POST
│   └── coas/              GET, POST
└── system/
    ├── audit-trail/       GET
    ├── health/            GET
    ├── backups/           GET, POST
    └── settings/          GET, PUT
```

#### Service Layer Architecture
```python
# services/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from sqlalchemy.orm import Session
from models.base import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseService(Generic[T], ABC):
    def __init__(self, db: Session, model_class: type[T]):
        self.db = db
        self.model_class = model_class

    def create(self, obj_in: dict) -> T:
        db_obj = self.model_class(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, id: int) -> Optional[T]:
        return self.db.query(self.model_class).filter(
            self.model_class.id == id
        ).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model_class).offset(skip).limit(limit).all()

    def update(self, db_obj: T, obj_in: dict) -> T:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
```

### Workflow Engine Architecture

```python
# workflow/engine.py
from enum import Enum
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

class WorkflowState(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

@dataclass
class WorkflowTransition:
    from_state: WorkflowState
    to_state: WorkflowState
    action: str
    required_role: str
    condition: Callable[[Any], bool] = None
    side_effect: Callable[[Any], None] = None

class WorkflowEngine:
    def __init__(self):
        self.transitions: Dict[str, List[WorkflowTransition]] = {}
        self.state_handlers: Dict[WorkflowState, Callable] = {}

    def register_transition(self, workflow_type: str, transition: WorkflowTransition):
        if workflow_type not in self.transitions:
            self.transitions[workflow_type] = []
        self.transitions[workflow_type].append(transition)

    def can_transition(self, workflow_type: str, current_state: WorkflowState, 
                      action: str, user_role: str, context: Any = None) -> bool:
        transitions = self.transitions.get(workflow_type, [])
        for transition in transitions:
            if (transition.from_state == current_state and 
                transition.action == action and
                transition.required_role == user_role):
                if transition.condition:
                    return transition.condition(context)
                return True
        return False

    def execute_transition(self, workflow_type: str, current_state: WorkflowState,
                          action: str, user_role: str, context: Any = None) -> WorkflowState:
        if not self.can_transition(workflow_type, current_state, action, user_role, context):
            raise ValueError(f"Invalid transition: {current_state} -> {action}")
        
        transitions = self.transitions.get(workflow_type, [])
        for transition in transitions:
            if (transition.from_state == current_state and 
                transition.action == action and
                transition.required_role == user_role):
                if transition.side_effect:
                    transition.side_effect(context)
                return transition.to_state
        
        raise ValueError("Transition not found")

# Example EDMS workflow configuration
def setup_edms_workflow(engine: WorkflowEngine):
    # Author submits for review
    engine.register_transition("edms_document", WorkflowTransition(
        from_state=WorkflowState.DRAFT,
        to_state=WorkflowState.PENDING_REVIEW,
        action="submit_for_review",
        required_role="author"
    ))
    
    # Reviewer approves
    engine.register_transition("edms_document", WorkflowTransition(
        from_state=WorkflowState.PENDING_REVIEW,
        to_state=WorkflowState.REVIEWED,
        action="approve_review",
        required_role="reviewer"
    ))
    
    # Reviewer rejects
    engine.register_transition("edms_document", WorkflowTransition(
        from_state=WorkflowState.PENDING_REVIEW,
        to_state=WorkflowState.DRAFT,
        action="reject_review",
        required_role="reviewer"
    ))
    
    # Submit for final approval
    engine.register_transition("edms_document", WorkflowTransition(
        from_state=WorkflowState.REVIEWED,
        to_state=WorkflowState.PENDING_APPROVAL,
        action="submit_for_approval",
        required_role="author"
    ))
    
    # Final approval
    engine.register_transition("edms_document", WorkflowTransition(
        from_state=WorkflowState.PENDING_APPROVAL,
        to_state=WorkflowState.APPROVED,
        action="approve_final",
        required_role="approver"
    ))
```

## Security Architecture

### Authentication & Authorization

#### JWT Token Structure
```python
# auth/jwt.py
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def create_access_token(self, data: Dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
```

#### Role-Based Access Control (RBAC)
```python
# auth/rbac.py
from enum import Enum
from typing import Set, Dict, List
from functools import wraps
from fastapi import HTTPException, Depends

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    REVIEW = "review"
    APPROVE = "approve"
    ADMIN = "admin"

class Module(Enum):
    EDMS = "edms"
    QRM = "qrm"
    TRM = "trm"
    LIMS = "lims"
    SYSTEM = "system"

class Role:
    def __init__(self, name: str, permissions: Set[Permission], modules: Set[Module]):
        self.name = name
        self.permissions = permissions
        self.modules = modules

# Predefined roles
ROLES = {
    "system_admin": Role("System Admin", {Permission.ADMIN}, {Module.SYSTEM}),
    "edms_viewer": Role("EDMS Viewer", {Permission.READ}, {Module.EDMS}),
    "edms_author": Role("EDMS Author", {Permission.READ, Permission.WRITE}, {Module.EDMS}),
    "edms_reviewer": Role("EDMS Reviewer", {Permission.READ, Permission.WRITE, Permission.REVIEW}, {Module.EDMS}),
    "edms_approver": Role("EDMS Approver", {Permission.READ, Permission.WRITE, Permission.REVIEW, Permission.APPROVE}, {Module.EDMS}),
    "quality_viewer": Role("Quality Viewer", {Permission.READ}, {Module.QRM}),
    "quality_responsible": Role("Quality Responsible", {Permission.READ, Permission.WRITE}, {Module.QRM}),
    "quality_reviewer": Role("Quality Reviewer", {Permission.READ, Permission.WRITE, Permission.REVIEW}, {Module.QRM}),
    "quality_approver": Role("Quality Approver", {Permission.READ, Permission.WRITE, Permission.REVIEW, Permission.APPROVE}, {Module.QRM}),
}

def require_permission(module: Module, permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from JWT token
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check if user has required permission for module
            user_roles = current_user.get('roles', [])
            has_permission = False
            
            for role_name in user_roles:
                role = ROLES.get(role_name)
                if role and module in role.modules and permission in role.permissions:
                    has_permission = True
                    break
            
            if not has_permission:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Digital Signature Implementation

```python
# security/digital_signature.py
import hashlib
import base64
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography import x509

class DigitalSignatureService:
    def __init__(self, private_key_path: str, certificate_path: str, password: str):
        self.private_key = self._load_private_key(private_key_path, password)
        self.certificate = self._load_certificate(certificate_path)

    def _load_private_key(self, key_path: str, password: str):
        with open(key_path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=password.encode() if password else None
            )

    def _load_certificate(self, cert_path: str):
        with open(cert_path, "rb") as cert_file:
            return x509.load_pem_x509_certificate(cert_file.read())

    def sign_document(self, document_path: str, metadata: dict) -> dict:
        # Calculate document hash
        with open(document_path, "rb") as doc_file:
            document_data = doc_file.read()
        
        document_hash = hashlib.sha256(document_data).hexdigest()
        
        # Create signature data
        signature_data = {
            "document_hash": document_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "signer": {
                "name": metadata.get("signer_name"),
                "email": metadata.get("signer_email"),
                "reason": metadata.get("reason", "Document approval")
            },
            "certificate_info": {
                "subject": str(self.certificate.subject),
                "issuer": str(self.certificate.issuer),
                "serial_number": str(self.certificate.serial_number)
            }
        }
        
        # Sign the hash
        signature_payload = f"{document_hash}{signature_data['timestamp']}"
        signature = self.private_key.sign(
            signature_payload.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        signature_data["signature"] = base64.b64encode(signature).decode()
        return signature_data

    def verify_signature(self, document_path: str, signature_data: dict) -> bool:
        try:
            # Recalculate document hash
            with open(document_path, "rb") as doc_file:
                document_data = doc_file.read()
            
            document_hash = hashlib.sha256(document_data).hexdigest()
            
            # Verify hash matches
            if document_hash != signature_data["document_hash"]:
                return False
            
            # Verify signature
            signature_payload = f"{document_hash}{signature_data['timestamp']}"
            signature = base64.b64decode(signature_data["signature"])
            
            public_key = self.certificate.public_key()
            public_key.verify(
                signature,
                signature_payload.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
```

### Audit Trail Implementation

```python
# audit/trail.py
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Dict, Any
import json

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW
    table_name = Column(String(100), nullable=False)
    record_id = Column(String(100))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(100))
    module = Column(String(50))  # EDMS, QRM, TRM, LIMS, SYSTEM
    reason = Column(Text)

class AuditService:
    def __init__(self, db_session):
        self.db = db_session

    def log_action(self, user_id: int, username: str, action: str, 
                   table_name: str, record_id: str = None, 
                   old_values: Dict = None, new_values: Dict = None,
                   ip_address: str = None, user_agent: str = None,
                   session_id: str = None, module: str = None,
                   reason: str = None):
        
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            module=module,
            reason=reason
        )
        
        self.db.add(audit_log)
        self.db.commit()

    def get_audit_trail(self, table_name: str = None, record_id: str = None,
                       user_id: int = None, start_date: datetime = None,
                       end_date: datetime = None, limit: int = 100):
        
        query = self.db.query(AuditLog)
        
        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        if record_id:
            query = query.filter(AuditLog.record_id == record_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

# Decorator for automatic audit logging
def audit_action(action: str, table_name: str, module: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user info from request context
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Log the action
            if current_user and hasattr(request, 'app'):
                audit_service = request.app.state.audit_service
                audit_service.log_action(
                    user_id=current_user['user_id'],
                    username=current_user['username'],
                    action=action,
                    table_name=table_name,
                    record_id=getattr(result, 'id', None) if hasattr(result, 'id') else None,
                    ip_address=request.client.host if hasattr(request, 'client') else None,
                    user_agent=request.headers.get('user-agent') if hasattr(request, 'headers') else None,
                    module=module
                )
            
            return result
        return wrapper
    return decorator
```

This is the first part of the comprehensive technical documentation. The file covers the core architecture, infrastructure setup, security implementation, and workflow engine. 

Would you like me to continue with the remaining sections including:
1. **Database schema design** with detailed entity relationships
2. **API specifications** with complete endpoint documentation  
3. **Module-specific implementation details** for EDMS, QRM, TRM, and LIMS
4. **Validation strategies** for 21 CFR Part 11 compliance
5. **Deployment procedures** and operational guides?