# QMS Base Model
# Phase 1: Base model with common fields for all entities

from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
import uuid

from app.core.database import Base


class BaseModel(Base):
    """Base model class with common fields for all entities"""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        return cls.__name__.lower() + 's'
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp (UTC)"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp (UTC)"
    )
    
    version = Column(
        Integer, 
        default=1, 
        nullable=False,
        comment="Record version for optimistic locking"
    )
    
    is_deleted = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Soft delete flag"
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, uuid={self.uuid})>"
    
    def to_dict(self, exclude_fields=None):
        """Convert model instance to dictionary"""
        exclude_fields = exclude_fields or []
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if hasattr(value, 'isoformat'):  # datetime objects
                    result[column.name] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
        
        return result
    
    @classmethod
    def get_table_name(cls):
        """Get the table name for this model"""
        return cls.__tablename__
