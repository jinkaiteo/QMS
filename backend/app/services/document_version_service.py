"""
Document Version Control Service
Manages document versioning, numbering, and lifecycle
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.user import User
from app.models.edms import Document, DocumentType, DocumentCategory
from app.models.document_complete import DocumentVersion, DocumentStatus
from app.services.document_storage_service import document_storage_service


class DocumentVersionService:
    """Service for managing document versions and lifecycle"""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
    
    def create_new_version(
        self,
        document_id: int,
        file_data: bytes,
        filename: str,
        change_summary: str,
        version_type: str = "minor"  # major, minor, revision
    ) -> DocumentVersion:
        """Create a new version of an existing document"""
        
        # Get original document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        # Get current latest version
        latest_version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.is_current == True
        ).first()
        
        # Calculate new version number
        new_version_number = self._calculate_next_version(
            latest_version.version_number if latest_version else "1.0",
            version_type
        )
        
        # Upload new file version
        file_path, file_info = self._upload_version_file(
            file_data, filename, document, new_version_number
        )
        
        # Mark previous version as not current
        if latest_version:
            latest_version.is_current = False
        
        # Create new version record
        new_version = DocumentVersion(
            document_id=document_id,
            version_number=new_version_number,
            file_path=file_path,
            file_name=filename,
            file_size=file_info["size"],
            mime_type=file_info["content_type"],
            file_hash=file_info["hash"],
            change_summary=change_summary,
            created_by_id=self.current_user.id,
            is_current=True
        )
        
        self.db.add(new_version)
        
        # Update document record
        document.current_version = new_version_number
        document.file_path = file_path
        document.file_name = filename
        document.file_size = file_info["size"]
        document.mime_type = file_info["content_type"]
        document.file_hash = file_info["hash"]
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(new_version)
        
        return new_version
    
    def supersede_document(
        self,
        old_document_id: int,
        new_document_id: int,
        supersession_reason: str
    ) -> bool:
        """Mark a document as superseded by another document"""
        
        old_document = self.db.query(Document).filter(Document.id == old_document_id).first()
        new_document = self.db.query(Document).filter(Document.id == new_document_id).first()
        
        if not old_document or not new_document:
            raise ValueError("Document(s) not found")
        
        # Update old document
        old_document.status = DocumentStatus.SUPERSEDED
        old_document.supersedes_document_id = new_document_id
        old_document.retirement_reason = supersession_reason
        old_document.updated_at = datetime.utcnow()
        
        # Update new document relationship
        new_document.supersedes_document_id = old_document_id
        
        self.db.commit()
        return True
    
    def retire_document(
        self,
        document_id: int,
        retirement_reason: str,
        effective_date: Optional[datetime] = None
    ) -> bool:
        """Retire a document from active use"""
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        # Update document status
        document.status = DocumentStatus.RETIRED
        document.retirement_reason = retirement_reason
        document.expiry_date = effective_date or datetime.utcnow()
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def generate_document_number(
        self,
        document_type_id: int,
        category_id: Optional[int] = None
    ) -> str:
        """Generate a controlled document number"""
        
        document_type = self.db.query(DocumentType).filter(
            DocumentType.id == document_type_id
        ).first()
        
        if not document_type:
            raise ValueError("Document type not found")
        
        # Get prefix from document type
        prefix = document_type.prefix or document_type.code
        
        # Add category prefix if available
        if category_id:
            category = self.db.query(DocumentCategory).filter(
                DocumentCategory.id == category_id
            ).first()
            if category:
                prefix = f"{prefix}-{category.code}"
        
        # Get current year
        year = datetime.utcnow().year
        
        # Find next sequence number for this prefix/year combination
        pattern = f"{prefix}-{year}-%"
        latest_doc = self.db.query(Document).filter(
            Document.document_number.like(pattern)
        ).order_by(desc(Document.document_number)).first()
        
        if latest_doc and latest_doc.document_number:
            # Extract sequence number
            match = re.search(r'-(\d+)$', latest_doc.document_number)
            if match:
                next_seq = int(match.group(1)) + 1
            else:
                next_seq = 1
        else:
            next_seq = 1
        
        # Generate document number
        document_number = f"{prefix}-{year}-{next_seq:04d}"
        
        return document_number
    
    def get_version_history(self, document_id: int) -> List[Dict[str, Any]]:
        """Get complete version history for a document"""
        
        versions = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.created_at)).all()
        
        version_history = []
        for version in versions:
            version_info = {
                "id": version.id,
                "version_number": version.version_number,
                "file_name": version.file_name,
                "file_size": version.file_size,
                "change_summary": version.change_summary,
                "created_by": version.created_by.username if version.created_by else None,
                "created_at": version.created_at,
                "approved_by": version.approved_by.username if version.approved_by else None,
                "approved_at": version.approved_at,
                "is_current": version.is_current,
                "file_hash": version.file_hash
            }
            version_history.append(version_info)
        
        return version_history
    
    def compare_versions(
        self,
        document_id: int,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Compare two versions of a document"""
        
        v1 = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version1
        ).first()
        
        v2 = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version2
        ).first()
        
        if not v1 or not v2:
            raise ValueError("Version(s) not found")
        
        comparison = {
            "document_id": document_id,
            "version1": {
                "version_number": v1.version_number,
                "file_name": v1.file_name,
                "file_size": v1.file_size,
                "file_hash": v1.file_hash,
                "created_at": v1.created_at,
                "created_by": v1.created_by.username if v1.created_by else None,
                "change_summary": v1.change_summary
            },
            "version2": {
                "version_number": v2.version_number,
                "file_name": v2.file_name,
                "file_size": v2.file_size,
                "file_hash": v2.file_hash,
                "created_at": v2.created_at,
                "created_by": v2.created_by.username if v2.created_by else None,
                "change_summary": v2.change_summary
            },
            "differences": {
                "file_name_changed": v1.file_name != v2.file_name,
                "file_size_changed": v1.file_size != v2.file_size,
                "content_changed": v1.file_hash != v2.file_hash,
                "size_difference_bytes": (v2.file_size or 0) - (v1.file_size or 0)
            }
        }
        
        return comparison
    
    def get_document_genealogy(self, document_id: int) -> Dict[str, Any]:
        """Get document family tree (superseded/supersedes relationships)"""
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        genealogy = {
            "current_document": {
                "id": document.id,
                "title": document.title,
                "document_number": document.document_number,
                "status": document.status,
                "current_version": document.current_version
            },
            "supersedes": [],
            "superseded_by": [],
            "related_documents": []
        }
        
        # Find documents this document supersedes
        if document.supersedes_document_id:
            superseded_doc = self.db.query(Document).filter(
                Document.id == document.supersedes_document_id
            ).first()
            if superseded_doc:
                genealogy["supersedes"].append({
                    "id": superseded_doc.id,
                    "title": superseded_doc.title,
                    "document_number": superseded_doc.document_number,
                    "status": superseded_doc.status,
                    "retirement_reason": superseded_doc.retirement_reason
                })
        
        # Find documents that supersede this document
        superseding_docs = self.db.query(Document).filter(
            Document.supersedes_document_id == document_id
        ).all()
        
        for superseding_doc in superseding_docs:
            genealogy["superseded_by"].append({
                "id": superseding_doc.id,
                "title": superseding_doc.title,
                "document_number": superseding_doc.document_number,
                "status": superseding_doc.status
            })
        
        return genealogy
    
    def archive_document(
        self,
        document_id: int,
        archive_reason: str,
        retention_years: Optional[int] = None
    ) -> bool:
        """Archive a document for long-term storage"""
        
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        # Calculate retention period
        if not retention_years:
            doc_type = document.document_type
            retention_years = doc_type.retention_period_years if doc_type else 7
        
        # Update document for archival
        document.status = DocumentStatus.RETIRED
        document.retirement_reason = archive_reason
        document.expiry_date = datetime.utcnow() + timedelta(days=retention_years * 365)
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def get_lifecycle_metrics(self, document_type_id: Optional[int] = None) -> Dict[str, Any]:
        """Get document lifecycle metrics and statistics"""
        
        query = self.db.query(Document)
        if document_type_id:
            query = query.filter(Document.document_type_id == document_type_id)
        
        # Status distribution
        status_counts = {}
        for status in DocumentStatus:
            count = query.filter(Document.status == status).count()
            status_counts[status.value] = count
        
        # Version statistics
        total_documents = query.count()
        total_versions = self.db.query(DocumentVersion).count()
        avg_versions_per_doc = total_versions / total_documents if total_documents > 0 else 0
        
        # Recently updated documents
        recent_updates = query.filter(
            Document.updated_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Documents needing review
        review_due = query.filter(
            Document.review_due_date <= datetime.utcnow(),
            Document.status.in_([DocumentStatus.APPROVED, DocumentStatus.PUBLISHED])
        ).count()
        
        return {
            "total_documents": total_documents,
            "status_distribution": status_counts,
            "version_statistics": {
                "total_versions": total_versions,
                "average_versions_per_document": round(avg_versions_per_doc, 2)
            },
            "recent_activity": {
                "updated_last_30_days": recent_updates,
                "documents_needing_review": review_due
            }
        }
    
    # Private helper methods
    
    def _calculate_next_version(self, current_version: str, version_type: str) -> str:
        """Calculate the next version number"""
        
        try:
            parts = current_version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            revision = int(parts[2]) if len(parts) > 2 else 0
            
            if version_type == "major":
                return f"{major + 1}.0"
            elif version_type == "minor":
                return f"{major}.{minor + 1}"
            elif version_type == "revision":
                if len(parts) < 3:
                    return f"{major}.{minor}.1"
                else:
                    return f"{major}.{minor}.{revision + 1}"
            else:
                return f"{major}.{minor + 1}"
                
        except (ValueError, IndexError):
            return "1.0"
    
    def _upload_version_file(
        self,
        file_data: bytes,
        filename: str,
        document: Document,
        version_number: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Upload a new version file to storage"""
        
        # Create a mock UploadFile for the storage service
        class MockUploadFile:
            def __init__(self, data: bytes, name: str, content_type: str):
                self.filename = name
                self.content_type = content_type
                self.size = len(data)
                self._data = data
            
            async def read(self):
                return self._data
        
        # Determine content type
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        
        mock_file = MockUploadFile(file_data, filename, content_type or "application/octet-stream")
        
        # Upload using document storage service
        file_path, file_info = document_storage_service.upload_file(
            file=mock_file,
            document_type=document.document_type.code.lower() if document.document_type else "general",
            metadata={
                "document_id": document.id,
                "version": version_number,
                "title": document.title
            }
        )
        
        return file_path, file_info