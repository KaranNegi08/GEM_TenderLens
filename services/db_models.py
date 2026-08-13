"""
SQLAlchemy ORM Models for GeM TenderLens.
Maps transactional database tables for audit logging, reviewer sign-offs, and tender workspace tracking.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, JSON, Boolean
from services.database import Base


class AuditLogORM(Base):
    """ORM mapping for AuditLog table."""
    __tablename__ = "audit_logs"

    log_id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    actor = Column(String(128), nullable=False, index=True)
    action_type = Column(String(128), nullable=False, index=True)
    details = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AuditLogORM(log_id='{self.log_id}', actor='{self.actor}', action_type='{self.action_type}')>"


class ReviewerActionORM(Base):
    """ORM mapping for human reviewer sign-off actions."""
    __tablename__ = "reviewer_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(256), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    reviewer_comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<ReviewerActionORM(finding_id='{self.finding_id}', action='{self.action}')>"


class TenderWorkspaceORM(Base):
    """ORM mapping for tender workspace tracking."""
    __tablename__ = "tender_workspaces"

    tender_id = Column(String(128), primary_key=True, index=True)
    title = Column(String(256), nullable=True)
    status = Column(String(64), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<TenderWorkspaceORM(tender_id='{self.tender_id}', status='{self.status}')>"


class TenderRequirementORM(Base):
    """ORM mapping for dynamically extracted tender requirements."""
    __tablename__ = "tender_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_id = Column(String(128), index=True, nullable=False)
    tender_id = Column(String(128), index=True, nullable=False)
    clause_id = Column(String(128), nullable=True)
    requirement_text = Column(Text, nullable=False)
    requirement_type = Column(String(64), default="technical")
    is_mandatory = Column(Boolean, default=True)
    evidence_required = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<TenderRequirementORM(requirement_id='{self.requirement_id}', tender_id='{self.tender_id}')>"


class VendorSubmissionORM(Base):
    """ORM mapping for vendor submission revisions."""
    __tablename__ = "vendor_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(String(64), index=True, nullable=False)
    vendor_name = Column(String(256), nullable=False)
    tender_id = Column(String(128), index=True, nullable=False)
    revision_number = Column(Integer, nullable=False, default=1)
    quoted_amount = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    delivery_days = Column(Integer, nullable=True)
    warranty_months = Column(Integer, nullable=True)
    full_text_snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<VendorSubmissionORM(vendor_id='{self.vendor_id}', tender_id='{self.tender_id}', rev={self.revision_number})>"


