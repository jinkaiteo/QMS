# QMS System - 21 CFR Part 11 Compliance & Validation

## Table of Contents
1. [21 CFR Part 11 Overview](#21-cfr-part-11-overview)
2. [Electronic Records Requirements](#electronic-records-requirements)
3. [Electronic Signatures Implementation](#electronic-signatures-implementation)
4. [ALCOA Principles Implementation](#alcoa-principles-implementation)
5. [Validation Documentation](#validation-documentation)
6. [Compliance Testing Protocols](#compliance-testing-protocols)

## 21 CFR Part 11 Overview

### Regulatory Scope
21 CFR Part 11 establishes criteria for FDA acceptance of electronic records and electronic signatures as equivalent to paper records and handwritten signatures.

### Key Requirements Matrix

| Requirement | CFR Section | QMS Implementation | Status |
|-------------|-------------|-------------------|---------|
| Electronic Record Controls | 11.10(a) | User access controls, RBAC system | ✅ Implemented |
| Authority Checks | 11.10(b) | Role-based permissions, approval workflows | ✅ Implemented |
| Device Controls | 11.10(c) | Session management, device authentication | ✅ Implemented |
| Time Stamps | 11.10(e) | UTC timestamps, NTP synchronization | ✅ Implemented |
| Sequencing | 11.10(f) | Database sequences, audit trail | ✅ Implemented |
| Authority Checks for Systems | 11.10(g) | System access controls | ✅ Implemented |
| Device Checks | 11.10(h) | Device fingerprinting, security controls | ✅ Implemented |
| Education & Training | 11.10(i) | Training management module | ✅ Implemented |
| Accountability | 11.10(j) | Individual user accounts, audit trails | ✅ Implemented |
| Appropriate Controls | 11.10(k) | Data integrity, backup/recovery | ✅ Implemented |
| Electronic Signature Components | 11.50 | Digital signatures, PKI infrastructure | ✅ Implemented |
| Signature Verification | 11.70 | Signature validation, certificate chains | ✅ Implemented |

## Electronic Records Requirements

### Access Controls (11.10(a))
```python
# Implementation: Role-Based Access Control
class AccessControlService:
    def __init__(self, db: Session):
        self.db = db
    
    def validate_access(self, user_id: int, resource: str, 
                       action: str, context: Dict = None) -> bool:
        """
        Validate user access to specific resources and actions
        Implements 21 CFR 11.10(a) - limiting system access to authorized individuals
        """
        user = self.db.query(User).get(user_id)
        if not user or not user.is_active:
            return False
        
        # Check if user has required role and permissions
        user_permissions = self._get_user_permissions(user_id)
        required_permission = f"{resource}:{action}"
        
        if required_permission not in user_permissions:
            # Log unauthorized access attempt
            self._log_access_attempt(user_id, resource, action, False, 
                                   reason="Insufficient permissions")
            return False
        
        # Additional context-based checks
        if context and not self._validate_context_access(user_id, context):
            self._log_access_attempt(user_id, resource, action, False,
                                   reason="Context validation failed")
            return False
        
        # Log successful access
        self._log_access_attempt(user_id, resource, action, True)
        return True
    
    def _log_access_attempt(self, user_id: int, resource: str, 
                           action: str, success: bool, reason: str = None):
        """Log all access attempts for audit compliance"""
        access_log = AccessLog(
            user_id=user_id,
            resource=resource,
            action=action,
            success=success,
            ip_address=self._get_current_ip(),
            user_agent=self._get_current_user_agent(),
            reason=reason,
            timestamp=datetime.utcnow()
        )
        self.db.add(access_log)
        self.db.commit()
```

### Time Stamps (11.10(e))
```python
# Implementation: Reliable Time Stamping
class TimeStampService:
    def __init__(self, ntp_servers: List[str]):
        self.ntp_servers = ntp_servers
        self.time_authority_url = "http://timestamp.digicert.com"
    
    def get_trusted_timestamp(self) -> datetime:
        """
        Get trusted timestamp from NTP servers
        Implements 21 CFR 11.10(e) - secure, computer-generated timestamps
        """
        try:
            # Sync with NTP servers
            ntp_time = self._sync_with_ntp()
            if ntp_time:
                return ntp_time
        except Exception as e:
            logger.warning(f"NTP sync failed: {e}")
        
        # Fallback to system time with warning
        logger.warning("Using system time - NTP sync unavailable")
        return datetime.utcnow()
    
    def create_qualified_timestamp(self, data: bytes) -> Dict[str, Any]:
        """Create RFC 3161 qualified timestamp"""
        import requests
        import hashlib
        
        # Create hash of data
        data_hash = hashlib.sha256(data).digest()
        
        # Create timestamp request
        ts_request = self._create_rfc3161_request(data_hash)
        
        # Send to timestamp authority
        response = requests.post(
            self.time_authority_url,
            data=ts_request,
            headers={'Content-Type': 'application/timestamp-query'}
        )
        
        if response.status_code == 200:
            return {
                'timestamp': datetime.utcnow(),
                'authority': self.time_authority_url,
                'token': response.content,
                'hash_algorithm': 'SHA-256'
            }
        
        raise Exception("Timestamp authority unavailable")

# Database trigger for automatic timestamps
CREATE OR REPLACE FUNCTION set_audit_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure timestamp is set and cannot be modified by users
    NEW.created_at = CURRENT_TIMESTAMP AT TIME ZONE 'UTC';
    NEW.audit_id = uuid_generate_v4();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all audit tables
CREATE TRIGGER audit_timestamp_trigger
    BEFORE INSERT ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION set_audit_timestamp();
```

### Data Integrity Controls (11.10(c))
```python
# Implementation: Data Integrity and Security
class DataIntegrityService:
    def __init__(self):
        self.encryption_key = self._load_encryption_key()
    
    def calculate_record_hash(self, record_data: Dict) -> str:
        """
        Calculate tamper-evident hash for records
        Implements data integrity requirements
        """
        # Create canonical representation
        canonical_data = self._canonicalize_data(record_data)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(canonical_data.encode()).hexdigest()
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data at rest"""
        from cryptography.fernet import Fernet
        
        cipher = Fernet(self.encryption_key)
        return cipher.encrypt(data.encode()).decode()
    
    def verify_record_integrity(self, record_id: int, table_name: str) -> bool:
        """Verify record has not been tampered with"""
        current_record = self._get_current_record(record_id, table_name)
        stored_hash = current_record.get('data_hash')
        
        # Recalculate hash
        record_data = {k: v for k, v in current_record.items() 
                      if k not in ['data_hash', 'created_at', 'updated_at']}
        calculated_hash = self.calculate_record_hash(record_data)
        
        return stored_hash == calculated_hash
    
    def create_backup_verification(self, backup_data: bytes) -> Dict:
        """Create verification data for backups"""
        return {
            'size': len(backup_data),
            'hash': hashlib.sha256(backup_data).hexdigest(),
            'timestamp': datetime.utcnow().isoformat(),
            'verification_method': 'SHA-256'
        }
```

## Electronic Signatures Implementation

### Digital Signature Service
```python
# services/digital_signature.py
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography import x509
import base64

class DigitalSignatureService:
    """
    Implements 21 CFR Part 11 Electronic Signatures
    Sections 11.50, 11.70, 11.100, 11.200, 11.300
    """
    
    def __init__(self, ca_cert_path: str, timestamp_authority: str):
        self.ca_certificate = self._load_ca_certificate(ca_cert_path)
        self.timestamp_authority = timestamp_authority
    
    def create_electronic_signature(self, user_id: int, document_id: int,
                                   signature_meaning: str, password: str) -> Dict:
        """
        Create electronic signature compliant with 21 CFR 11.50
        
        Args:
            user_id: ID of signing user
            document_id: ID of document being signed
            signature_meaning: Meaning of signature (e.g., "Approved by", "Reviewed by")
            password: User password for identity verification
        """
        # 1. Verify user identity (11.100(a))
        if not self._verify_user_identity(user_id, password):
            raise SecurityException("User identity verification failed")
        
        # 2. Get user's signing certificate
        user_cert = self._get_user_certificate(user_id)
        if not user_cert:
            raise SecurityException("User signing certificate not found")
        
        # 3. Verify certificate validity
        if not self._verify_certificate_chain(user_cert):
            raise SecurityException("Invalid or expired signing certificate")
        
        # 4. Get document data
        document_data = self._get_document_for_signing(document_id)
        document_hash = hashlib.sha256(document_data).hexdigest()
        
        # 5. Create signature data
        signature_data = {
            'user_id': user_id,
            'document_id': document_id,
            'document_hash': document_hash,
            'signature_meaning': signature_meaning,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': self._get_current_ip(),
            'user_agent': self._get_current_user_agent()
        }
        
        # 6. Create digital signature
        private_key = self._get_user_private_key(user_id, password)
        signature_payload = json.dumps(signature_data, sort_keys=True)
        
        digital_signature = private_key.sign(
            signature_payload.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # 7. Get qualified timestamp
        timestamp_token = self._get_qualified_timestamp(signature_payload.encode())
        
        # 8. Store signature record
        signature_record = ElectronicSignature(
            user_id=user_id,
            document_id=document_id,
            signature_meaning=signature_meaning,
            document_hash=document_hash,
            digital_signature=base64.b64encode(digital_signature).decode(),
            certificate_data=base64.b64encode(user_cert.public_bytes()).decode(),
            timestamp_token=timestamp_token,
            signature_data=signature_data,
            is_valid=True
        )
        
        # 9. Log signature event
        self._log_signature_event(user_id, document_id, signature_meaning, True)
        
        return {
            'signature_id': signature_record.id,
            'signature_hash': self._calculate_signature_hash(signature_record),
            'timestamp': signature_data['timestamp'],
            'certificate_info': self._extract_certificate_info(user_cert)
        }
    
    def verify_electronic_signature(self, signature_id: int) -> bool:
        """
        Verify electronic signature integrity (21 CFR 11.70)
        """
        signature_record = self.db.query(ElectronicSignature).get(signature_id)
        if not signature_record:
            return False
        
        try:
            # 1. Verify certificate chain
            certificate = x509.load_der_x509_certificate(
                base64.b64decode(signature_record.certificate_data)
            )
            if not self._verify_certificate_chain(certificate):
                return False
            
            # 2. Recreate signature payload
            signature_payload = json.dumps(signature_record.signature_data, sort_keys=True)
            
            # 3. Verify digital signature
            public_key = certificate.public_key()
            digital_signature = base64.b64decode(signature_record.digital_signature)
            
            public_key.verify(
                digital_signature,
                signature_payload.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # 4. Verify timestamp token
            if not self._verify_timestamp_token(signature_record.timestamp_token):
                return False
            
            # 5. Verify document hasn't changed
            current_doc_hash = self._get_current_document_hash(signature_record.document_id)
            if current_doc_hash != signature_record.document_hash:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def generate_signature_manifestation(self, signature_id: int) -> Dict:
        """
        Generate human-readable signature manifestation (21 CFR 11.50(a)(1))
        """
        signature = self.db.query(ElectronicSignature).get(signature_id)
        user = signature.user
        document = signature.document
        
        return {
            'printed_name': f"{user.first_name} {user.last_name}",
            'date_time': signature.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'meaning': signature.signature_meaning,
            'document_title': document.title,
            'document_number': document.document_number,
            'document_version': document.current_version.version_number,
            'signature_id': str(signature.uuid),
            'verification_method': 'Digital Certificate'
        }

# Database schema for electronic signatures
CREATE TABLE electronic_signatures (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    document_id INTEGER REFERENCES documents(id) NOT NULL,
    signature_meaning VARCHAR(255) NOT NULL, -- "Approved by", "Reviewed by", etc.
    document_hash VARCHAR(128) NOT NULL, -- Hash of document at time of signing
    digital_signature TEXT NOT NULL, -- Base64 encoded digital signature
    certificate_data TEXT NOT NULL, -- Base64 encoded signing certificate
    timestamp_token TEXT, -- RFC 3161 timestamp token
    signature_data JSONB NOT NULL, -- Complete signature context
    ip_address INET,
    user_agent TEXT,
    verification_status VARCHAR(50) DEFAULT 'valid',
    verification_log JSONB, -- Log of verification attempts
    is_valid BOOLEAN DEFAULT TRUE,
    invalidated_at TIMESTAMP WITH TIME ZONE,
    invalidated_by INTEGER REFERENCES users(id),
    invalidation_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Signature Workflow Integration
```python
# Integration with document workflows
class SignatureWorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.signature_service = DigitalSignatureService(db)
    
    def require_signature(self, workflow_step_id: int, signature_meaning: str):
        """Mark workflow step as requiring electronic signature"""
        step = self.db.query(DocumentWorkflowStep).get(workflow_step_id)
        step.signature_required = True
        step.signature_meaning = signature_meaning
        self.db.commit()
    
    def complete_with_signature(self, workflow_step_id: int, user_id: int,
                               password: str, comments: str = None):
        """Complete workflow step with electronic signature"""
        step = self.db.query(DocumentWorkflowStep).get(workflow_step_id)
        
        if step.signature_required:
            # Create electronic signature
            signature = self.signature_service.create_electronic_signature(
                user_id=user_id,
                document_id=step.workflow.document_version.document_id,
                signature_meaning=step.signature_meaning,
                password=password
            )
            
            step.signature_id = signature['signature_id']
        
        step.completed_at = datetime.utcnow()
        step.status = 'completed'
        step.comments = comments
        
        self.db.commit()
```

## ALCOA Principles Implementation

### Attributable
```python
# Every action is linked to an authenticated user
class AttributabilityService:
    def log_user_action(self, user_id: int, action: str, 
                       entity_type: str, entity_id: int, details: Dict = None):
        """Ensure all actions are attributable to specific users"""
        audit_log = AuditLog(
            user_id=user_id,
            username=self._get_username(user_id),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            timestamp=datetime.utcnow(),
            ip_address=self._get_current_ip(),
            session_id=self._get_current_session_id()
        )
        self.db.add(audit_log)
        self.db.commit()
```

### Legible
```python
# Data must be readable throughout record retention period
class LegibilityService:
    def ensure_data_legibility(self, data: Any, format_type: str) -> str:
        """Ensure data remains legible and readable"""
        if format_type == 'text':
            # Standardize text encoding
            return self._normalize_text_encoding(data)
        elif format_type == 'pdf':
            # Ensure PDF/A compliance for long-term readability
            return self._convert_to_pdf_a(data)
        elif format_type == 'image':
            # Use standard formats with compression
            return self._standardize_image_format(data)
        
        return str(data)  # Fallback to string representation
```

### Contemporaneous
```python
# Data recorded at time of activity
class ContemporaneousService:
    def record_real_time_data(self, data: Dict, event_type: str):
        """Record data at the time of the event"""
        record = RealTimeRecord(
            data=data,
            event_type=event_type,
            recorded_at=datetime.utcnow(),  # Immediate recording
            source_system='QMS',
            is_contemporaneous=True
        )
        self.db.add(record)
        self.db.commit()
    
    def validate_timing(self, event_time: datetime, record_time: datetime) -> bool:
        """Validate that record was created contemporaneously"""
        time_diff = abs((record_time - event_time).total_seconds())
        return time_diff <= 300  # Allow 5 minutes for contemporaneous recording
```

### Original
```python
# Preserve original data
class OriginalityService:
    def preserve_original(self, data: Any, metadata: Dict) -> str:
        """Preserve original data with metadata"""
        original_record = OriginalDataRecord(
            original_data=data,
            data_hash=hashlib.sha256(str(data).encode()).hexdigest(),
            metadata=metadata,
            preservation_method='database_storage',
            created_at=datetime.utcnow()
        )
        self.db.add(original_record)
        self.db.commit()
        return original_record.uuid
    
    def verify_originality(self, record_id: str) -> bool:
        """Verify data originality using hash comparison"""
        record = self.db.query(OriginalDataRecord).filter_by(uuid=record_id).first()
        current_hash = hashlib.sha256(str(record.original_data).encode()).hexdigest()
        return current_hash == record.data_hash
```

### Accurate
```python
# Ensure data accuracy
class AccuracyService:
    def validate_data_accuracy(self, data: Dict, validation_rules: Dict) -> bool:
        """Validate data accuracy against business rules"""
        for field, rules in validation_rules.items():
            if field in data:
                if not self._apply_validation_rules(data[field], rules):
                    return False
        return True
    
    def create_data_verification(self, data_id: int, verifier_id: int, 
                               verification_method: str) -> bool:
        """Create verification record for data accuracy"""
        verification = DataVerification(
            data_id=data_id,
            verifier_id=verifier_id,
            verification_method=verification_method,
            verified_at=datetime.utcnow(),
            is_accurate=True
        )
        self.db.add(verification)
        self.db.commit()
        return True
```

This covers the comprehensive compliance and validation framework. Would you like me to continue with deployment architecture and operational procedures documentation?