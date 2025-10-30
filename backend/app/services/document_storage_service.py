"""
Document Storage Service
MinIO integration for file upload and management
"""

import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, BinaryIO
from pathlib import Path
import mimetypes

from minio import Minio
from minio.error import S3Error
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.models.edms import Document, DocumentVersion
from app.models.user import User


class DocumentStorageService:
    """Service for handling document storage operations with MinIO"""
    
    def __init__(self):
        # MinIO connection configuration
        self.client = Minio(
            endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ROOT_USER', 'minioadmin'),
            secret_key=os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'),
            secure=False  # Set to True for HTTPS
        )
        
        # Default bucket for documents
        self.bucket_name = os.getenv('MINIO_DOCUMENTS_BUCKET', 'qms-documents')
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the documents bucket exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def generate_file_path(self, filename: str, document_type: str = "general") -> str:
        """Generate a structured file path for storage"""
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        # Generate unique filename to prevent collisions
        file_extension = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{file_extension}"
        
        return f"{document_type}/{year}/{month}/{day}/{unique_name}"
    
    def calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_data).hexdigest()
    
    def get_file_metadata(self, file: UploadFile) -> dict:
        """Extract metadata from uploaded file"""
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size if hasattr(file, 'size') else None,
        }
    
    async def upload_file(
        self, 
        file: UploadFile, 
        document_type: str = "general",
        metadata: Optional[dict] = None
    ) -> Tuple[str, dict]:
        """
        Upload a file to MinIO storage
        Returns: (file_path, file_info)
        """
        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Generate storage path
            storage_path = self.generate_file_path(file.filename, document_type)
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_content)
            
            # Prepare metadata
            file_metadata = {
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size": file_size,
                "hash": file_hash,
                "upload_date": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Upload to MinIO
            from io import BytesIO
            file_stream = BytesIO(file_content)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                data=file_stream,
                length=file_size,
                content_type=file.content_type,
                metadata=file_metadata
            )
            
            return storage_path, {
                "file_path": storage_path,
                "original_filename": file.filename,
                "size": file_size,
                "content_type": file.content_type,
                "hash": file_hash,
                "bucket": self.bucket_name
            }
            
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")
    
    def download_file(self, file_path: str) -> Tuple[bytes, dict]:
        """Download a file from MinIO storage"""
        try:
            response = self.client.get_object(self.bucket_name, file_path)
            file_data = response.read()
            
            # Get object metadata
            stat = self.client.stat_object(self.bucket_name, file_path)
            
            metadata = {
                "content_type": stat.content_type,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "metadata": stat.metadata or {}
            }
            
            return file_data, metadata
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise HTTPException(status_code=404, detail="File not found")
            raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from MinIO storage"""
        try:
            self.client.remove_object(self.bucket_name, file_path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False  # File already doesn't exist
            raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")
    
    def list_files(self, prefix: str = "", limit: int = 100) -> List[dict]:
        """List files in storage with optional prefix filter"""
        try:
            objects = self.client.list_objects(
                self.bucket_name, 
                prefix=prefix, 
                recursive=True
            )
            
            files = []
            count = 0
            for obj in objects:
                if count >= limit:
                    break
                    
                files.append({
                    "file_path": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
                count += 1
            
            return files
            
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"List error: {str(e)}")
    
    def generate_presigned_url(
        self, 
        file_path: str, 
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate a presigned URL for temporary file access"""
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                file_path,
                expires=expires
            )
            return url
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"Presigned URL error: {str(e)}")
    
    def validate_file_type(self, filename: str, allowed_types: List[str] = None) -> bool:
        """Validate file type against allowed types"""
        if allowed_types is None:
            # Default allowed types for pharmaceutical documents
            allowed_types = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.ppt', '.pptx', '.txt', '.csv', '.png', 
                '.jpg', '.jpeg', '.gif', '.zip'
            ]
        
        file_extension = Path(filename).suffix.lower()
        return file_extension in allowed_types
    
    def validate_file_size(self, file_size: int, max_size_mb: int = 50) -> bool:
        """Validate file size against maximum allowed size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes


# Global service instance
document_storage_service = DocumentStorageService()