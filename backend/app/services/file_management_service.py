"""
File Management Service
Handles document file upload, download, and version management with MinIO storage
"""
import os
import hashlib
import mimetypes
from datetime import datetime
from typing import List, Optional, Dict, Any, BinaryIO
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class FileManagementService:
    """Service for managing document files with MinIO storage"""
    
    def __init__(self, db: Session):
        self.db = db
        self.bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'qms-documents')
        
        # Initialize MinIO client
        if MINIO_AVAILABLE:
            try:
                self.minio_client = Minio(
                    endpoint=getattr(settings, 'MINIO_ENDPOINT', 'qms-minio-prod:9000'),
                    access_key=getattr(settings, 'MINIO_ROOT_USER', 'minio'),
                    secret_key=getattr(settings, 'MINIO_ROOT_PASSWORD', 'minio123'),
                    secure=getattr(settings, 'MINIO_SECURE', False)
                )
                self._ensure_bucket_exists()
                self.storage_available = True
                logger.info("MinIO client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MinIO client: {str(e)}")
                self.storage_available = False
        else:
            logger.warning("MinIO not available - using local file storage")
            self.storage_available = False
            self._setup_local_storage()
    
    def _ensure_bucket_exists(self):
        """Ensure the documents bucket exists"""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {str(e)}")
            raise
    
    def _setup_local_storage(self):
        """Setup local file storage as fallback"""
        self.local_storage_path = Path(getattr(settings, 'LOCAL_STORAGE_PATH', '/tmp/qms_documents'))
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage setup at: {self.local_storage_path}")
    
    def upload_document_file(
        self,
        document_id: int,
        file_content: BinaryIO,
        filename: str,
        user_id: int,
        version_number: Optional[str] = None,
        upload_reason: str = "File upload"
    ) -> Dict[str, Any]:
        """Upload a document file and create version record"""
        try:
            # Read file content and calculate checksum
            file_content.seek(0)
            content = file_content.read()
            file_size = len(content)
            checksum = hashlib.sha256(content).hexdigest()
            
            # Determine MIME type
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            # Generate version number if not provided
            if not version_number:
                version_number = self._generate_next_version(document_id)
            
            # Parse version number
            major_version, minor_version = self._parse_version_number(version_number)
            
            # Generate file path in storage
            file_path = self._generate_file_path(document_id, version_number, filename)
            
            # Upload to storage
            if self.storage_available:
                storage_path = self._upload_to_minio(file_path, content)
            else:
                storage_path = self._upload_to_local(file_path, content)
            
            # Create document version record
            version_data = {
                'document_id': document_id,
                'version_number': version_number,
                'major_version': major_version,
                'minor_version': minor_version,
                'file_path': storage_path,
                'file_name': filename,
                'file_size': file_size,
                'mime_type': mime_type,
                'checksum': checksum,
                'uploaded_by_id': user_id,
                'upload_reason': upload_reason,
                'is_current': True  # Will trigger database trigger to unset others
            }
            
            version_id = self._create_document_version(version_data)
            
            logger.info(f"File uploaded successfully for document {document_id}, version {version_number}")
            
            return {
                'version_id': version_id,
                'version_number': version_number,
                'file_path': storage_path,
                'file_size': file_size,
                'checksum': checksum,
                'mime_type': mime_type
            }
            
        except Exception as e:
            logger.error(f"Error uploading file for document {document_id}: {str(e)}")
            raise
    
    def download_document_file(
        self,
        document_id: int,
        version_number: Optional[str] = None,
        download_type: str = 'original'
    ) -> Dict[str, Any]:
        """Download a document file"""
        try:
            # Get version info
            if version_number:
                version_info = self._get_version_by_number(document_id, version_number)
            else:
                version_info = self._get_current_version(document_id)
            
            if not version_info:
                raise ValueError(f"Version not found for document {document_id}")
            
            file_path = version_info['file_path']
            filename = version_info['file_name']
            
            # Handle different download types
            if download_type == 'official_pdf':
                # Generate official PDF if document is approved
                if self._is_document_approved(document_id):
                    file_content = self._generate_official_pdf(document_id, version_info)
                    filename = filename.replace('.docx', '.pdf').replace('.doc', '.pdf')
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                else:
                    raise ValueError("Official PDF only available for approved documents")
            else:
                # Download original or annotated file
                if self.storage_available:
                    file_content = self._download_from_minio(file_path)
                else:
                    file_content = self._download_from_local(file_path)
            
            return {
                'content': file_content,
                'filename': filename,
                'mime_type': version_info['mime_type'],
                'file_size': len(file_content) if file_content else 0,
                'version_number': version_info['version_number']
            }
            
        except Exception as e:
            logger.error(f"Error downloading file for document {document_id}: {str(e)}")
            raise
    
    def get_document_versions(self, document_id: int) -> List[Dict[str, Any]]:
        """Get all versions for a document"""
        try:
            query = text("""
                SELECT 
                    dv.id,
                    dv.version_number,
                    dv.major_version,
                    dv.minor_version,
                    dv.file_name,
                    dv.file_size,
                    dv.mime_type,
                    dv.is_current,
                    dv.is_official,
                    dv.upload_reason,
                    dv.created_at,
                    u.username as uploaded_by
                FROM document_versions dv
                JOIN users u ON dv.uploaded_by_id = u.id
                WHERE dv.document_id = :document_id 
                  AND dv.is_deleted = FALSE
                ORDER BY dv.major_version DESC, dv.minor_version DESC
            """)
            
            result = self.db.execute(query, {'document_id': document_id})
            versions = []
            
            for row in result.fetchall():
                versions.append({
                    'id': row.id,
                    'version_number': row.version_number,
                    'major_version': row.major_version,
                    'minor_version': row.minor_version,
                    'file_name': row.file_name,
                    'file_size': row.file_size,
                    'mime_type': row.mime_type,
                    'is_current': row.is_current,
                    'is_official': row.is_official,
                    'upload_reason': row.upload_reason,
                    'created_at': row.created_at,
                    'uploaded_by': row.uploaded_by
                })
            
            return versions
            
        except Exception as e:
            logger.error(f"Error getting versions for document {document_id}: {str(e)}")
            return []
    
    def delete_document_version(
        self,
        version_id: int,
        user_id: int,
        reason: str = "Version deletion"
    ) -> bool:
        """Soft delete a document version"""
        try:
            # Check if it's the current version
            query = text("""
                SELECT is_current, file_path FROM document_versions 
                WHERE id = :version_id AND is_deleted = FALSE
            """)
            
            result = self.db.execute(query, {'version_id': version_id})
            row = result.fetchone()
            
            if not row:
                raise ValueError("Version not found")
            
            if row.is_current:
                raise ValueError("Cannot delete current version")
            
            # Soft delete the version
            delete_query = text("""
                UPDATE document_versions 
                SET is_deleted = TRUE, updated_at = NOW()
                WHERE id = :version_id
            """)
            
            self.db.execute(delete_query, {'version_id': version_id})
            self.db.commit()
            
            # Optionally delete from storage (for now just mark as deleted)
            logger.info(f"Version {version_id} soft deleted by user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting version {version_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def create_document_dependency(
        self,
        parent_document_id: int,
        dependent_document_id: int,
        dependency_type: str,
        user_id: int,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a dependency relationship between documents"""
        try:
            # Check for circular dependencies
            if self._would_create_circular_dependency(parent_document_id, dependent_document_id):
                raise ValueError("This dependency would create a circular reference")
            
            query = text("""
                INSERT INTO document_dependencies 
                (parent_document_id, dependent_document_id, dependency_type, created_by_id, notes, created_at, updated_at)
                VALUES (:parent_id, :dependent_id, :dep_type, :created_by, :notes, NOW(), NOW())
                RETURNING id
            """)
            
            result = self.db.execute(query, {
                'parent_id': parent_document_id,
                'dependent_id': dependent_document_id,
                'dep_type': dependency_type,
                'created_by': user_id,
                'notes': notes
            })
            
            dependency_id = result.fetchone()[0]
            self.db.commit()
            
            logger.info(f"Dependency created: {parent_document_id} -> {dependent_document_id} ({dependency_type})")
            
            return {
                'dependency_id': dependency_id,
                'parent_document_id': parent_document_id,
                'dependent_document_id': dependent_document_id,
                'dependency_type': dependency_type
            }
            
        except Exception as e:
            logger.error(f"Error creating dependency: {str(e)}")
            self.db.rollback()
            raise
    
    def get_document_dependencies(
        self,
        document_id: int,
        direction: str = 'both'  # 'parent', 'dependent', or 'both'
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get dependencies for a document"""
        try:
            dependencies = {'parents': [], 'dependents': []}
            
            if direction in ['parent', 'both']:
                # Get documents this one depends on
                parent_query = text("""
                    SELECT 
                        dd.id as dependency_id,
                        dd.dependency_type,
                        dd.notes,
                        d.id as document_id,
                        d.document_number,
                        d.title,
                        d.status,
                        u.username as created_by
                    FROM document_dependencies dd
                    JOIN documents d ON dd.parent_document_id = d.id
                    JOIN users u ON dd.created_by_id = u.id
                    WHERE dd.dependent_document_id = :document_id 
                      AND dd.is_deleted = FALSE
                      AND d.is_deleted = FALSE
                    ORDER BY dd.created_at DESC
                """)
                
                result = self.db.execute(parent_query, {'document_id': document_id})
                for row in result.fetchall():
                    dependencies['parents'].append({
                        'dependency_id': row.dependency_id,
                        'dependency_type': row.dependency_type,
                        'notes': row.notes,
                        'document_id': row.document_id,
                        'document_number': row.document_number,
                        'title': row.title,
                        'status': row.status,
                        'created_by': row.created_by
                    })
            
            if direction in ['dependent', 'both']:
                # Get documents that depend on this one
                dependent_query = text("""
                    SELECT 
                        dd.id as dependency_id,
                        dd.dependency_type,
                        dd.notes,
                        d.id as document_id,
                        d.document_number,
                        d.title,
                        d.status,
                        u.username as created_by
                    FROM document_dependencies dd
                    JOIN documents d ON dd.dependent_document_id = d.id
                    JOIN users u ON dd.created_by_id = u.id
                    WHERE dd.parent_document_id = :document_id 
                      AND dd.is_deleted = FALSE
                      AND d.is_deleted = FALSE
                    ORDER BY dd.created_at DESC
                """)
                
                result = self.db.execute(dependent_query, {'document_id': document_id})
                for row in result.fetchall():
                    dependencies['dependents'].append({
                        'dependency_id': row.dependency_id,
                        'dependency_type': row.dependency_type,
                        'notes': row.notes,
                        'document_id': row.document_id,
                        'document_number': row.document_number,
                        'title': row.title,
                        'status': row.status,
                        'created_by': row.created_by
                    })
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error getting dependencies for document {document_id}: {str(e)}")
            return {'parents': [], 'dependents': []}
    
    # Private helper methods
    
    def _generate_next_version(self, document_id: int) -> str:
        """Generate the next version number for a document"""
        try:
            query = text("""
                SELECT major_version, minor_version 
                FROM document_versions 
                WHERE document_id = :document_id AND is_deleted = FALSE
                ORDER BY major_version DESC, minor_version DESC 
                LIMIT 1
            """)
            
            result = self.db.execute(query, {'document_id': document_id})
            row = result.fetchone()
            
            if row:
                # Increment minor version
                major, minor = row.major_version, row.minor_version
                return f"{major}.{minor + 1}"
            else:
                # First version
                return "1.0"
                
        except Exception:
            return "1.0"
    
    def _parse_version_number(self, version_number: str) -> tuple:
        """Parse version number into major and minor components"""
        try:
            parts = version_number.split('.')
            major = int(parts[0]) if parts[0] else 1
            minor = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            return major, minor
        except (ValueError, IndexError):
            return 1, 0
    
    def _generate_file_path(self, document_id: int, version_number: str, filename: str) -> str:
        """Generate storage path for a file"""
        # Structure: documents/{document_id}/v{version_number}/{filename}
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '.-_')
        return f"documents/{document_id}/v{version_number}/{safe_filename}"
    
    def _upload_to_minio(self, file_path: str, content: bytes) -> str:
        """Upload file to MinIO storage"""
        try:
            from io import BytesIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=BytesIO(content),
                length=len(content)
            )
            return f"minio://{self.bucket_name}/{file_path}"
        except S3Error as e:
            logger.error(f"MinIO upload error: {str(e)}")
            raise
    
    def _upload_to_local(self, file_path: str, content: bytes) -> str:
        """Upload file to local storage"""
        try:
            full_path = self.local_storage_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(content)
            
            return f"local://{full_path}"
        except Exception as e:
            logger.error(f"Local storage upload error: {str(e)}")
            raise
    
    def _download_from_minio(self, file_path: str) -> bytes:
        """Download file from MinIO storage"""
        try:
            # Extract object name from path
            object_name = file_path.replace(f"minio://{self.bucket_name}/", "")
            
            response = self.minio_client.get_object(self.bucket_name, object_name)
            content = response.read()
            response.close()
            return content
        except S3Error as e:
            logger.error(f"MinIO download error: {str(e)}")
            raise
    
    def _download_from_local(self, file_path: str) -> bytes:
        """Download file from local storage"""
        try:
            # Extract local path
            local_path = file_path.replace("local://", "")
            
            with open(local_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Local storage download error: {str(e)}")
            raise
    
    def _create_document_version(self, version_data: Dict[str, Any]) -> int:
        """Create a document version record"""
        query = text("""
            INSERT INTO document_versions 
            (document_id, version_number, major_version, minor_version, file_path, file_name, 
             file_size, mime_type, checksum, uploaded_by_id, upload_reason, is_current, created_at, updated_at)
            VALUES (:document_id, :version_number, :major_version, :minor_version, :file_path, :file_name,
                    :file_size, :mime_type, :checksum, :uploaded_by_id, :upload_reason, :is_current, NOW(), NOW())
            RETURNING id
        """)
        
        result = self.db.execute(query, version_data)
        version_id = result.fetchone()[0]
        self.db.commit()
        return version_id
    
    def _get_version_by_number(self, document_id: int, version_number: str) -> Optional[Dict[str, Any]]:
        """Get version info by version number"""
        query = text("""
            SELECT id, version_number, file_path, file_name, mime_type, file_size
            FROM document_versions 
            WHERE document_id = :document_id AND version_number = :version_number AND is_deleted = FALSE
        """)
        
        result = self.db.execute(query, {'document_id': document_id, 'version_number': version_number})
        row = result.fetchone()
        
        if row:
            return {
                'id': row.id,
                'version_number': row.version_number,
                'file_path': row.file_path,
                'file_name': row.file_name,
                'mime_type': row.mime_type,
                'file_size': row.file_size
            }
        return None
    
    def _get_current_version(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get current version info"""
        query = text("""
            SELECT id, version_number, file_path, file_name, mime_type, file_size
            FROM document_versions 
            WHERE document_id = :document_id AND is_current = TRUE AND is_deleted = FALSE
        """)
        
        result = self.db.execute(query, {'document_id': document_id})
        row = result.fetchone()
        
        if row:
            return {
                'id': row.id,
                'version_number': row.version_number,
                'file_path': row.file_path,
                'file_name': row.file_name,
                'mime_type': row.mime_type,
                'file_size': row.file_size
            }
        return None
    
    def _is_document_approved(self, document_id: int) -> bool:
        """Check if document is approved"""
        query = text("SELECT status FROM documents WHERE id = :document_id")
        result = self.db.execute(query, {'document_id': document_id})
        row = result.fetchone()
        return row and row.status == 'approved'
    
    def _generate_official_pdf(self, document_id: int, version_info: Dict[str, Any]) -> bytes:
        """Generate official PDF with metadata and signatures (placeholder)"""
        # This is a placeholder - in a real implementation, you would:
        # 1. Convert the original document to PDF
        # 2. Add metadata headers/footers
        # 3. Add digital signatures
        # 4. Add approval stamps
        
        logger.info(f"Generating official PDF for document {document_id}")
        
        # For now, return a simple PDF placeholder
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 128
>>
stream
BT
/F1 12 Tf
72 720 Td
(Official QMS Document) Tj
0 -14 Td
(Document ID: """ + str(document_id).encode() + b""") Tj
0 -14 Td
(Version: """ + version_info['version_number'].encode() + b""") Tj
0 -14 Td
(Status: APPROVED) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
386
%%EOF"""
        
        return pdf_content
    
    def _would_create_circular_dependency(self, parent_id: int, dependent_id: int) -> bool:
        """Check if adding a dependency would create a circular reference"""
        # Simple check - in a real implementation, you would do a more thorough graph traversal
        if parent_id == dependent_id:
            return True
        
        # Check if dependent_id is already a parent of parent_id
        query = text("""
            SELECT COUNT(*) FROM document_dependencies 
            WHERE parent_document_id = :dependent_id AND dependent_document_id = :parent_id
            AND is_deleted = FALSE
        """)
        
        result = self.db.execute(query, {'dependent_id': dependent_id, 'parent_id': parent_id})
        count = result.fetchone()[0]
        
        return count > 0