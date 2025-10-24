# QMS System - Module Implementation Guide

## Table of Contents
1. [EDMS Implementation](#edms-implementation)
2. [QRM Implementation](#qrm-implementation)
3. [TRM Implementation](#trm-implementation)
4. [LIMS Implementation](#lims-implementation)
5. [Cross-Module Integration](#cross-module-integration)

## EDMS Implementation

### Core Components

#### Document Service Layer
```python
# services/edms/document_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.edms import Document, DocumentVersion, DocumentWorkflow
from services.base import BaseService
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService

class DocumentService(BaseService[Document]):
    def __init__(self, db: Session):
        super().__init__(db, Document)
        self.workflow_service = WorkflowService(db)
        self.notification_service = NotificationService(db)

    def create_document(self, document_data: Dict[str, Any], file_data: bytes, 
                       filename: str, user_id: int) -> Document:
        """Create a new document with initial version"""
        
        # Generate document number
        doc_number = self._generate_document_number(document_data['document_type_id'])
        
        # Create document record
        document = Document(
            document_number=doc_number,
            title=document_data['title'],
            description=document_data.get('description'),
            document_type_id=document_data['document_type_id'],
            category_id=document_data.get('category_id'),
            source_type=document_data['source_type'],
            author_id=user_id,
            status='draft'
        )
        
        self.db.add(document)
        self.db.flush()  # Get document ID
        
        # Create initial version
        version = self._create_document_version(
            document.id, "1.0", 1, 0, file_data, filename, user_id
        )
        
        # Set current version
        document.current_version_id = version.id
        self.db.commit()
        
        return document

    def _generate_document_number(self, document_type_id: int) -> str:
        """Generate unique document number based on type and sequence"""
        doc_type = self.db.query(DocumentType).get(document_type_id)
        prefix = doc_type.prefix or doc_type.code
        
        # Get next sequence number
        last_doc = self.db.query(Document)\
            .filter(Document.document_number.like(f"{prefix}%"))\
            .order_by(Document.id.desc())\
            .first()
        
        if last_doc:
            # Extract sequence from last document number
            last_seq = int(last_doc.document_number.split('-')[-1])
            seq = last_seq + 1
        else:
            seq = 1
        
        return f"{prefix}-{seq:05d}"

    def start_review_workflow(self, document_id: int, reviewer_id: int, 
                             user_id: int, due_date: datetime = None) -> DocumentWorkflow:
        """Start document review workflow"""
        
        document = self.get(document_id)
        if not document or document.status != 'draft':
            raise ValueError("Document not eligible for review")
        
        # Create workflow
        workflow = DocumentWorkflow(
            document_version_id=document.current_version_id,
            workflow_type='review',
            current_state='pending_review',
            initiated_by=user_id,
            due_date=due_date
        )
        
        self.db.add(workflow)
        self.db.flush()
        
        # Create workflow steps
        self.workflow_service.create_workflow_step(
            workflow.id, 1, "Document Review", reviewer_id, due_date
        )
        
        # Update document status
        document.status = 'pending_review'
        
        # Send notification
        self.notification_service.send_notification(
            recipient_id=reviewer_id,
            title=f"Document Review Required: {document.title}",
            message=f"Please review document {document.document_number}",
            entity_type='document',
            entity_id=document_id
        )
        
        self.db.commit()
        return workflow

    def approve_document(self, workflow_id: int, approver_id: int, 
                        effective_date: date, user_id: int) -> bool:
        """Approve document and set effective date"""
        
        workflow = self.db.query(DocumentWorkflow).get(workflow_id)
        if not workflow or workflow.current_state != 'reviewed':
            raise ValueError("Workflow not in reviewable state")
        
        document = workflow.document_version.document
        version = workflow.document_version
        
        # Update version
        version.approver_id = approver_id
        version.approved_at = datetime.utcnow()
        version.effective_date = effective_date
        version.status = 'approved'
        
        # Update document
        document.status = 'approved'
        
        # Complete workflow
        workflow.current_state = 'approved'
        workflow.completed_at = datetime.utcnow()
        
        # Create digital signature
        self._create_digital_signature(version.id, approver_id, 'approver')
        
        self.db.commit()
        return True

    def search_documents(self, query: str, filters: Dict = None, 
                        user_permissions: List[str] = None) -> List[Document]:
        """Advanced document search with full-text and metadata"""
        
        base_query = self.db.query(Document)\
            .filter(Document.is_deleted == False)
        
        # Full-text search
        if query:
            base_query = base_query.filter(
                or_(
                    Document.title.ilike(f'%{query}%'),
                    Document.description.ilike(f'%{query}%'),
                    Document.keywords.any(query.lower())
                )
            )
        
        # Apply filters
        if filters:
            if filters.get('document_type_id'):
                base_query = base_query.filter(
                    Document.document_type_id == filters['document_type_id']
                )
            
            if filters.get('status'):
                base_query = base_query.filter(
                    Document.status == filters['status']
                )
            
            if filters.get('author_id'):
                base_query = base_query.filter(
                    Document.author_id == filters['author_id']
                )
            
            if filters.get('created_from'):
                base_query = base_query.filter(
                    Document.created_at >= filters['created_from']
                )
            
            if filters.get('created_to'):
                base_query = base_query.filter(
                    Document.created_at <= filters['created_to']
                )
        
        # Apply permission-based filtering
        if user_permissions and 'admin' not in user_permissions:
            # Add logic for document visibility based on user permissions
            pass
        
        return base_query.order_by(Document.updated_at.desc()).all()
```

#### Document Processing Service
```python
# services/edms/document_processor.py
import hashlib
import mimetypes
from typing import Tuple, Dict, Any
from pathlib import Path
import zipfile
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class DocumentProcessor:
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def process_upload(self, file_data: bytes, filename: str, 
                      document_id: int, version: str) -> Dict[str, Any]:
        """Process uploaded document file"""
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Determine MIME type
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Generate storage path
        file_path = self._generate_file_path(document_id, version, filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Extract metadata
        metadata = self._extract_metadata(file_path, mime_type)
        
        return {
            'file_path': str(file_path),
            'file_size': len(file_data),
            'file_hash': file_hash,
            'file_mime_type': mime_type,
            'page_count': metadata.get('page_count'),
            'word_count': metadata.get('word_count')
        }

    def _extract_metadata(self, file_path: Path, mime_type: str) -> Dict[str, Any]:
        """Extract metadata from document"""
        metadata = {}
        
        try:
            if mime_type == 'application/pdf':
                with open(file_path, 'rb') as file:
                    pdf_reader = PdfReader(file)
                    metadata['page_count'] = len(pdf_reader.pages)
                    
            elif 'wordprocessingml.document' in mime_type:
                doc = DocxDocument(file_path)
                metadata['page_count'] = len(doc.sections)
                metadata['word_count'] = sum(
                    len(paragraph.text.split()) 
                    for paragraph in doc.paragraphs
                )
                
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Error extracting metadata: {e}")
        
        return metadata

    def generate_annotated_document(self, document_version, placeholders: Dict[str, str]) -> bytes:
        """Generate annotated document with metadata"""
        
        file_path = Path(document_version.file_path)
        mime_type = document_version.file_mime_type
        
        if 'wordprocessingml.document' in mime_type:
            return self._annotate_docx(file_path, placeholders)
        elif mime_type == 'application/pdf':
            return self._annotate_pdf(file_path, placeholders)
        else:
            # For other file types, return original with metadata file
            return self._create_metadata_package(file_path, placeholders)

    def _annotate_docx(self, file_path: Path, placeholders: Dict[str, str]) -> bytes:
        """Annotate DOCX document with metadata placeholders"""
        
        doc = DocxDocument(file_path)
        
        # Replace placeholders in document
        for paragraph in doc.paragraphs:
            for placeholder, value in placeholders.items():
                if placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(placeholder, value)
        
        # Add metadata to document properties
        doc.core_properties.title = placeholders.get('{{DOC_TITLE}}', '')
        doc.core_properties.author = placeholders.get('{{DOC_AUTHOR}}', '')
        doc.core_properties.subject = placeholders.get('{{DOC_NUMBER}}', '')
        
        # Save to bytes
        from io import BytesIO
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue()

    def generate_official_pdf(self, document_version, signature_data: Dict) -> bytes:
        """Generate official PDF with digital signature"""
        
        # First generate annotated document
        placeholders = self._build_placeholders(document_version)
        annotated_content = self.generate_annotated_document(document_version, placeholders)
        
        # Convert to PDF if not already PDF
        if document_version.file_mime_type != 'application/pdf':
            pdf_content = self._convert_to_pdf(annotated_content, document_version.file_mime_type)
        else:
            pdf_content = annotated_content
        
        # Apply digital signature
        signed_pdf = self._apply_digital_signature(pdf_content, signature_data)
        
        return signed_pdf

    def _build_placeholders(self, document_version) -> Dict[str, str]:
        """Build placeholder replacement dictionary"""
        
        doc = document_version.document
        
        return {
            '{{DOC_NUMBER}}': doc.document_number,
            '{{DOC_TITLE}}': doc.title,
            '{{DOC_VERSION}}': document_version.version_number,
            '{{DOC_AUTHOR}}': document_version.author.full_name,
            '{{DOC_REVIEWER}}': document_version.reviewer.full_name if document_version.reviewer else '',
            '{{DOC_APPROVER}}': document_version.approver.full_name if document_version.approver else '',
            '{{APPROVED_DATE}}': document_version.approved_at.strftime('%Y-%m-%d') if document_version.approved_at else '',
            '{{EFFECTIVE_DATE}}': document_version.effective_date.strftime('%Y-%m-%d') if document_version.effective_date else '',
            '{{DOWNLOAD_DATE}}': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            '{{DOC_STATUS}}': document_version.status.upper()
        }
```

### Frontend Components

#### Document List Component
```typescript
// components/edms/DocumentList.tsx
import React, { useState, useEffect } from 'react';
import {
  Table, TableBody, TableCell, TableHead, TableRow,
  Paper, TextField, Select, MenuItem, FormControl,
  InputLabel, Chip, IconButton, Tooltip, Box
} from '@mui/material';
import {
  Search, Download, Visibility, Edit, 
  Description, PictureAsPdf
} from '@mui/icons-material';
import { useDocumentService } from '../hooks/useDocumentService';

interface Document {
  id: number;
  uuid: string;
  document_number: string;
  title: string;
  document_type: {
    name: string;
    code: string;
  };
  status: string;
  current_version: string;
  author: {
    full_name: string;
  };
  approved_date?: string;
  effective_date?: string;
  tags: string[];
}

interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({ onDocumentSelect }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    document_type: '',
    status: '',
    page: 1,
    per_page: 20
  });
  
  const documentService = useDocumentService();

  useEffect(() => {
    loadDocuments();
  }, [filters]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await documentService.getDocuments(filters);
      setDocuments(response.data.items);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (documentId: number, versionId: number, type: string) => {
    try {
      const blob = await documentService.downloadDocument(documentId, versionId, type);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `document_${documentId}_${type}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading document:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      'draft': 'default',
      'pending_review': 'warning',
      'reviewed': 'info',
      'pending_approval': 'secondary',
      'approved': 'success',
      'rejected': 'error',
      'obsolete': 'default'
    };
    return colors[status] || 'default';
  };

  return (
    <Box>
      {/* Search and Filter Controls */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          label="Search documents"
          variant="outlined"
          size="small"
          value={filters.search}
          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
          InputProps={{
            startAdornment: <Search />
          }}
          sx={{ minWidth: 300 }}
        />
        
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Document Type</InputLabel>
          <Select
            value={filters.document_type}
            onChange={(e) => setFilters(prev => ({ ...prev, document_type: e.target.value }))}
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="sop">SOP</MenuItem>
            <MenuItem value="policy">Policy</MenuItem>
            <MenuItem value="manual">Manual</MenuItem>
            <MenuItem value="form">Form</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
          >
            <MenuItem value="">All Status</MenuItem>
            <MenuItem value="draft">Draft</MenuItem>
            <MenuItem value="approved">Approved</MenuItem>
            <MenuItem value="pending_review">Pending Review</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Document Table */}
      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Document Number</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Author</TableCell>
              <TableCell>Effective Date</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents.map((document) => (
              <TableRow 
                key={document.id}
                hover
                onClick={() => onDocumentSelect?.(document)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell>
                  <strong>{document.document_number}</strong>
                </TableCell>
                <TableCell>
                  <Box>
                    {document.title}
                    <Box sx={{ mt: 0.5 }}>
                      {document.tags.map((tag) => (
                        <Chip 
                          key={tag} 
                          label={tag} 
                          size="small" 
                          sx={{ mr: 0.5, fontSize: '0.7rem' }}
                        />
                      ))}
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{document.document_type.name}</TableCell>
                <TableCell>{document.current_version}</TableCell>
                <TableCell>
                  <Chip 
                    label={document.status}
                    color={getStatusColor(document.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{document.author.full_name}</TableCell>
                <TableCell>
                  {document.effective_date ? 
                    new Date(document.effective_date).toLocaleDateString() : 
                    '-'
                  }
                </TableCell>
                <TableCell>
                  <Tooltip title="View Document">
                    <IconButton size="small">
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Download Original">
                    <IconButton 
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(document.id, document.current_version_id, 'original');
                      }}
                    >
                      <Download />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Download Official PDF">
                    <IconButton 
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(document.id, document.current_version_id, 'official_pdf');
                      }}
                    >
                      <PictureAsPdf />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
};

export default DocumentList;
```

This covers the core EDMS implementation. Would you like me to continue with the QRM module implementation next, or focus on a different aspect of the system?