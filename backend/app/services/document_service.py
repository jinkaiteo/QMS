# Document Service - Phase 2 EDMS
# Core document management business logic

from typing import List, Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date
import hashlib
import mimetypes
import os
from pathlib import Path

from app.models.edms import (
    Document, DocumentVersion, DocumentType, DocumentCategory,
    DocumentWorkflow, WorkflowStep, DigitalSignature, DocumentComment
)
from app.models.user import User
from app.core.logging import get_audit_logger
from app.core.config import settings


class DocumentService:
    """Core document management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_logger = get_audit_logger()
        self.storage_path = Path(settings.DOCUMENT_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_document(
        self,
        title: str,
        document_type_id: int,
        file_data: bytes,
        filename: str,
        user_id: int,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        confidentiality_level: str = "internal"
    ) -> Document:
        """Create a new document with initial version"""
        
        # Generate document number
        doc_number = self._generate_document_number(document_type_id)
        
        # Process file upload
        file_info = self._process_file_upload(file_data, filename, doc_number, "1.0")
        
        # Create document record
        document = Document(
            document_number=doc_number,
            title=title,
            description=description,
            document_type_id=document_type_id,
            category_id=category_id,
            author_id=user_id,
            owner_id=user_id,
            keywords=keywords or [],
            tags=tags or [],
            confidentiality_level=confidentiality_level,
            status="draft"
        )
        
        self.db.add(document)
        self.db.flush()  # Get document ID
        
        # Create initial version
        version = DocumentVersion(
            document_id=document.id,
            version_number="1.0",
            major_version=1,
            minor_version=0,
            file_path=file_info["file_path"],
            file_name=filename,
            file_size=file_info["file_size"],
            file_hash=file_info["file_hash"],
            file_mime_type=file_info["mime_type"],
            page_count=file_info.get("page_count"),
            word_count=file_info.get("word_count"),
            author_id=user_id,
            status="draft"
        )
        
        self.db.add(version)
        self.db.flush()
        
        # Set current version
        document.current_version_id = version.id
        
        # Log the event
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="create",
            document_id=document.id,
            document_number=doc_number,
            details={"title": title, "file_name": filename}
        )
        
        self.db.commit()
        return document
    
    def get_document(self, document_id: int, user_id: int) -> Optional[Document]:
        """Get document by ID with permission check"""
        
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()
        
        if not document:
            return None
        
        # Check read permission
        if not self._check_document_permission(document, user_id, "read"):
            return None
        
        return document
    
    def search_documents(
        self,
        user_id: int,
        query: Optional[str] = None,
        document_type_id: Optional[int] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        author_id: Optional[int] = None,
        created_from: Optional[date] = None,
        created_to: Optional[date] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Search documents with filters and pagination"""
        
        base_query = self.db.query(Document).filter(
            Document.is_deleted == False
        )
        
        # Full-text search
        if query:
            base_query = base_query.filter(
                or_(
                    Document.title.ilike(f"%{query}%"),
                    Document.description.ilike(f"%{query}%"),
                    Document.document_number.ilike(f"%{query}%")
                )
            )
        
        # Apply filters
        if document_type_id:
            base_query = base_query.filter(Document.document_type_id == document_type_id)
        
        if category_id:
            base_query = base_query.filter(Document.category_id == category_id)
        
        if status:
            base_query = base_query.filter(Document.status == status)
        
        if author_id:
            base_query = base_query.filter(Document.author_id == author_id)
        
        if created_from:
            base_query = base_query.filter(Document.created_at >= created_from)
        
        if created_to:
            base_query = base_query.filter(Document.created_at <= created_to)
        
        # Apply permission filtering
        # For now, simple check - can be enhanced with complex permissions later
        accessible_docs = base_query.filter(
            or_(
                Document.author_id == user_id,
                Document.owner_id == user_id,
                Document.confidentiality_level.in_(["public", "internal"])
            )
        )
        
        # Get total count
        total = accessible_docs.count()
        
        # Apply pagination and ordering
        documents = accessible_docs.order_by(desc(Document.updated_at))\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return {
            "items": documents,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    def start_review_workflow(
        self,
        document_id: int,
        reviewer_id: int,
        user_id: int,
        due_date: Optional[date] = None,
        comments: Optional[str] = None
    ) -> DocumentWorkflow:
        """Start document review workflow"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            raise ValueError("Document not found or access denied")
        
        if document.status != "draft":
            raise ValueError("Document not eligible for review")
        
        # Check if user can initiate review
        if not self._check_document_permission(document, user_id, "review"):
            raise ValueError("Insufficient permissions to start review")
        
        # Create workflow
        workflow = DocumentWorkflow(
            document_version_id=document.current_version_id,
            workflow_type="review",
            workflow_name=f"Review for {document.document_number}",
            current_state="pending",
            initiated_by=user_id,
            assigned_to=reviewer_id,
            due_date=due_date,
            comments=comments,
            priority=2  # Medium priority
        )
        
        self.db.add(workflow)
        self.db.flush()
        
        # Create workflow step
        step = WorkflowStep(
            workflow_id=workflow.id,
            step_number=1,
            step_name="Document Review",
            assigned_to=reviewer_id,
            due_date=due_date,
            status="pending"
        )
        
        self.db.add(step)
        
        # Update document status
        document.status = "pending_review"
        
        # Log the event
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="start_review",
            document_id=document.id,
            document_number=document.document_number,
            details={"reviewer_id": reviewer_id, "due_date": str(due_date) if due_date else None}
        )
        
        self.db.commit()
        return workflow
    
    def complete_review(
        self,
        workflow_id: int,
        user_id: int,
        approved: bool,
        comments: Optional[str] = None
    ) -> bool:
        """Complete document review"""
        
        workflow = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == workflow_id,
            DocumentWorkflow.assigned_to == user_id,
            DocumentWorkflow.current_state == "pending"
        ).first()
        
        if not workflow:
            raise ValueError("Workflow not found or not assigned to user")
        
        # Update workflow
        workflow.current_state = "completed"
        workflow.completed_at = datetime.utcnow()
        workflow.comments = comments
        
        # Update workflow step
        step = self.db.query(WorkflowStep).filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.assigned_to == user_id,
            WorkflowStep.status == "pending"
        ).first()
        
        if step:
            step.status = "completed"
            step.completed_by = user_id
            step.completed_at = datetime.utcnow()
            step.comments = comments
        
        # Update document and version status
        document_version = workflow.document_version
        document = document_version.document
        
        if approved:
            document.status = "reviewed"
            document_version.status = "reviewed"
            document_version.reviewer_id = user_id
            document_version.reviewed_at = datetime.utcnow()
        else:
            document.status = "rejected"
            document_version.status = "rejected"
        
        # Log the event
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="complete_review",
            document_id=document.id,
            document_number=document.document_number,
            details={"approved": approved, "comments": comments}
        )
        
        self.db.commit()
        return True
    
    def approve_document(
        self,
        document_id: int,
        user_id: int,
        effective_date: date,
        comments: Optional[str] = None
    ) -> bool:
        """Approve document for release"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            raise ValueError("Document not found or access denied")
        
        if document.status != "reviewed":
            raise ValueError("Document must be reviewed before approval")
        
        # Check approval permission
        if not self._check_document_permission(document, user_id, "approve"):
            raise ValueError("Insufficient permissions to approve document")
        
        # Update document and version
        version = document.current_version
        version.approver_id = user_id
        version.approved_at = datetime.utcnow()
        version.effective_date = effective_date
        version.status = "approved"
        version.is_draft = False
        
        document.status = "approved"
        
        # Create digital signature
        self._create_digital_signature(
            version.id, user_id, "approver", "Approved for release"
        )
        
        # Log the event
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="approve",
            document_id=document.id,
            document_number=document.document_number,
            details={"effective_date": str(effective_date), "comments": comments}
        )
        
        self.db.commit()
        return True
    
    def download_document(
        self,
        document_id: int,
        version_id: Optional[int],
        user_id: int,
        download_type: str = "original"
    ) -> bytes:
        """Download document file"""
        
        document = self.get_document(document_id, user_id)
        if not document:
            raise ValueError("Document not found or access denied")
        
        # Get version
        if version_id:
            version = self.db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id,
                DocumentVersion.document_id == document_id
            ).first()
        else:
            version = document.current_version
        
        if not version:
            raise ValueError("Document version not found")
        
        # Check download permission
        if not self._check_document_permission(document, user_id, "download"):
            raise ValueError("Insufficient permissions to download document")
        
        # Read file
        file_path = Path(version.file_path)
        if not file_path.exists():
            raise ValueError("Document file not found on storage")
        
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Verify file integrity
        file_hash = hashlib.sha256(file_data).hexdigest()
        if file_hash != version.file_hash:
            raise ValueError("Document file integrity check failed")
        
        # Log download
        self.audit_logger.log_document_event(
            user_id=user_id,
            action="download",
            document_id=document.id,
            document_number=document.document_number,
            details={"version": version.version_number, "type": download_type}
        )
        
        return file_data
    
    def _generate_document_number(self, document_type_id: int) -> str:
        """Generate unique document number"""
        
        doc_type = self.db.query(DocumentType).get(document_type_id)
        if not doc_type:
            raise ValueError("Invalid document type")
        
        prefix = doc_type.prefix or doc_type.code
        
        # Get next sequence number
        last_doc = self.db.query(Document)\
            .filter(Document.document_number.like(f"{prefix}%"))\
            .order_by(desc(Document.id))\
            .first()
        
        if last_doc:
            # Extract sequence from last document number
            try:
                last_seq = int(last_doc.document_number.split("-")[-1])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}-{seq:05d}"
    
    def _process_file_upload(
        self, 
        file_data: bytes, 
        filename: str, 
        doc_number: str, 
        version: str
    ) -> Dict[str, Any]:
        """Process uploaded file and store it"""
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Determine MIME type
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        
        # Generate storage path
        file_path = self._generate_file_path(doc_number, version, filename)
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        # Extract metadata (basic implementation)
        metadata = self._extract_file_metadata(file_path, mime_type)
        
        return {
            "file_path": str(file_path),
            "file_size": len(file_data),
            "file_hash": file_hash,
            "mime_type": mime_type,
            **metadata
        }
    
    def _generate_file_path(self, doc_number: str, version: str, filename: str) -> Path:
        """Generate file storage path"""
        
        # Organize by year/month for better performance
        now = datetime.now()
        year_month = f"{now.year}/{now.month:02d}"
        
        # Create safe filename
        safe_filename = f"{doc_number}_v{version}_{filename}"
        
        return self.storage_path / year_month / safe_filename
    
    def _extract_file_metadata(self, file_path: Path, mime_type: str) -> Dict[str, Any]:
        """Extract metadata from file (basic implementation)"""
        
        metadata = {}
        
        try:
            if mime_type == "application/pdf":
                # PDF metadata extraction would go here
                # For now, just return empty metadata
                pass
            elif "wordprocessingml.document" in mime_type:
                # DOCX metadata extraction would go here
                pass
            
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Error extracting metadata: {e}")
        
        return metadata
    
    def _check_document_permission(
        self, 
        document: Document, 
        user_id: int, 
        permission: str
    ) -> bool:
        """Check if user has permission for document operation"""
        
        # Author/owner always has access
        if document.author_id == user_id or document.owner_id == user_id:
            return True
        
        # Check confidentiality level
        if permission == "read":
            if document.confidentiality_level in ["public", "internal"]:
                return True
        
        # TODO: Implement more sophisticated permission checking
        # based on roles, document permissions table, etc.
        
        return False
    
    def _create_digital_signature(
        self,
        document_version_id: int,
        user_id: int,
        signature_type: str,
        meaning: str
    ) -> DigitalSignature:
        """Create digital signature record"""
        
        # Generate signature hash (simplified - would use actual PKI in production)
        signature_data = f"{document_version_id}:{user_id}:{signature_type}:{meaning}:{datetime.utcnow()}"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        signature = DigitalSignature(
            document_version_id=document_version_id,
            signer_id=user_id,
            signature_type=signature_type,
            signature_meaning=meaning,
            signature_hash=signature_hash,
            signed_at=datetime.utcnow()
        )
        
        self.db.add(signature)
        
        # Log electronic signature
        self.audit_logger.log_electronic_signature(
            user_id=user_id,
            document_id=document_version_id,  # This should be fixed to use actual document ID
            signature_meaning=meaning,
            signature_hash=signature_hash
        )
        
        return signature