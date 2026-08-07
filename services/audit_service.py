"""
Audit & Database Service for GeM TenderLens.
Persists AuditLog and ReviewerAction entries to the transactional PostgreSQL database.
"""

from typing import List, Optional, Dict, Any
from schemas.audit import AuditLog, ReviewerAction
from services.database import get_db_session
from services.db_models import AuditLogORM, ReviewerActionORM
from utils_logger import get_logger

logger = get_logger(__name__)


class DatabaseAuditService:
    """Service layer for persisting and retrieving audit logs and reviewer sign-offs in database."""

    @staticmethod
    def save_audit_log(audit_log: AuditLog) -> bool:
        """Persists a Pydantic AuditLog instance into database."""
        try:
            with get_db_session() as session:
                orm_entry = AuditLogORM(
                    log_id=audit_log.log_id,
                    timestamp=audit_log.timestamp,
                    actor=audit_log.actor,
                    action_type=audit_log.action_type,
                    details=audit_log.details,
                )
                session.merge(orm_entry)
            logger.info(f"Persisted AuditLog {audit_log.log_id} to database.")
            return True
        except Exception as e:
            logger.error(f"Failed to save AuditLog {audit_log.log_id}: {e}")
            return False

    @staticmethod
    def save_reviewer_action(action: ReviewerAction) -> bool:
        """Persists a Pydantic ReviewerAction instance into database."""
        try:
            with get_db_session() as session:
                orm_entry = ReviewerActionORM(
                    finding_id=action.finding_id,
                    action=action.action,
                    reviewer_comments=action.reviewer_comments,
                    timestamp=action.timestamp,
                )
                session.add(orm_entry)
            logger.info(f"Persisted ReviewerAction for finding '{action.finding_id}' ({action.action}).")
            return True
        except Exception as e:
            logger.error(f"Failed to save ReviewerAction: {e}")
            return False

    @staticmethod
    def get_recent_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent audit logs from database."""
        try:
            with get_db_session() as session:
                entries = (
                    session.query(AuditLogORM)
                    .order_by(AuditLogORM.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                return [
                    {
                        "log_id": item.log_id,
                        "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                        "actor": item.actor,
                        "action_type": item.action_type,
                        "details": item.details or {},
                    }
                    for item in entries
                ]
        except Exception as e:
            logger.error(f"Failed to fetch audit logs: {e}")
            return []
