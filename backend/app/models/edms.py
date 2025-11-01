from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel

class DocumentType(BaseModel):
    __tablename__ = "document_types"
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    prefix = Column(String(10))
    is_active = Column(Boolean, default=True)

class DocumentCategory(BaseModel):
    __tablename__ = "document_categories"
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("document_categories.id"))
    is_active = Column(Boolean, default=True)

class Document(BaseModel):
    __tablename__ = "documents"

    title = Column(String(500), nullable=False)
    description = Column(Text)
    document_number = Column(String(100), unique=True)
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    file_hash = Column(String(64))
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("document_categories.id"))
    status = Column(String(50), default="draft")
    current_version = Column(String(20), default="1.0")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supersedes_document_id = Column(Integer, ForeignKey("documents.id"))
    effective_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    review_due_date = Column(DateTime(timezone=True))
    retirement_reason = Column(Text)
    is_controlled = Column(Boolean, default=True)
    confidentiality_level = Column(String(50), default="internal")
    
    # Relationships
    document_type = relationship("DocumentType")
    category = relationship("DocumentCategory")
    created_by = relationship("User", foreign_keys=[created_by_id])
    supersedes_document = relationship("Document", remote_side="Document.id")
    
    @classmethod
    def get_by_number(cls, db, document_number: str):
        return db.query(cls).filter(cls.document_number == document_number).first()
    
    @classmethod
    def get_by_type_and_category(cls, db, document_type_id: int, category_id: int = None):
        query = db.query(cls).filter(cls.document_type_id == document_type_id)
        if category_id:
            query = query.filter(cls.category_id == category_id)
        return query.all()