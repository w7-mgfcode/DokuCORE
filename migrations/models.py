from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Create a base class for declarative models
Base = declarative_base()

# Create SQLAlchemy models that match our database schema

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    # Note: We can't represent the vector type directly in SQLAlchemy
    # embedding = Column("embedding", ...)
    last_modified = Column(DateTime, server_default=func.now())
    version = Column(Integer, default=1)

class DocumentHistory(Base):
    __tablename__ = "document_history"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    content = Column(Text, nullable=False)
    changed_at = Column(DateTime, server_default=func.now())
    changed_by = Column(Text)
    version = Column(Integer, nullable=False)

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Text, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    code_path = Column(Text, nullable=True)

class DocumentHierarchy(Base):
    __tablename__ = "document_hierarchy"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    parent_id = Column(Integer, ForeignKey("document_hierarchy.id"), nullable=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    # embedding = Column("embedding", ...)
    doc_level = Column(Integer, nullable=False)
    seq_num = Column(Integer, nullable=False)

class DocumentRelationship(Base):
    __tablename__ = "document_relationships"
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("document_hierarchy.id"))
    target_id = Column(Integer, ForeignKey("document_hierarchy.id"))
    relationship_type = Column(Text, nullable=False)
    strength = Column(Float, nullable=False)

class DocumentKeyword(Base):
    __tablename__ = "document_keywords"
    
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("document_hierarchy.id"))
    keyword = Column(Text, nullable=False)
    # embedding = Column("embedding", ...)
    importance = Column(Float, nullable=False)