"""
Audit log schemas for GeM TenderLens.
Captures system events, reviewer decisions, and workflow audit trails.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from utils_logger import get_logger

logger = get_logger(__name__)

class ReviewerAction(BaseModel):
    """Captures human reviewer sign-off or status modification."""
    finding_id: str = Field(..., description="Target finding key vendor_id:requirement_id")
    action: str = Field(..., description="Action taken: approve, reject, flag_clarification")
    reviewer_comments: Optional[str] = Field(default=None, description="Reviewer feedback or notes")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of action")

class AuditLog(BaseModel):
    """System-wide audit entry for traceability."""
    log_id: str = Field(..., description="Unique log entry ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Log timestamp")
    actor: str = Field(..., description="User ID or Agent name e.g. Technical Compliance Agent")
    action_type: str = Field(..., description="Category e.g. TENDER_UPLOAD, COMPLIANCE_RUN, HUMAN_APPROVAL")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured event context")

    def __init__(self, **data):
        try:
            super().__init__(**data)
            logger.debug(f"Audit log created: {self.actor} - {self.action_type}")
        except Exception as e:
            logger.error(f"Failed to instantiate AuditLog: {e}")
            raise
