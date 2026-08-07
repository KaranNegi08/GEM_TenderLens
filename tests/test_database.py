"""
Unit tests for PostgreSQL/SQLAlchemy Database Integration and Audit Service.
"""

import pytest
from datetime import datetime
from schemas.audit import AuditLog, ReviewerAction
from services.database import init_db, get_engine
from services.audit_service import DatabaseAuditService


def test_database_initialization():
    """Verify that database engine initializes and tables are created."""
    engine = get_engine()
    assert engine is not None
    success = init_db()
    assert success is True


def test_audit_log_persistence():
    """Test saving and retrieving AuditLog objects via DatabaseAuditService."""
    init_db()
    test_log = AuditLog(
        log_id="test_log_001",
        timestamp=datetime.now(),
        actor="TestAgent",
        action_type="TEST_ACTION",
        details={"test_key": "test_value"}
    )
    
    saved = DatabaseAuditService.save_audit_log(test_log)
    assert saved is True

    logs = DatabaseAuditService.get_recent_audit_logs(limit=10)
    assert len(logs) > 0
    match = next((l for l in logs if l["log_id"] == "test_log_001"), None)
    assert match is not None
    assert match["actor"] == "TestAgent"
    assert match["action_type"] == "TEST_ACTION"
    assert match["details"] == {"test_key": "test_value"}


def test_reviewer_action_persistence():
    """Test saving ReviewerAction sign-off entries."""
    init_db()
    action = ReviewerAction(
        finding_id="vendor_xyz:req_101",
        action="approve",
        reviewer_comments="Technical specification fully compliant.",
        timestamp=datetime.now()
    )

    saved = DatabaseAuditService.save_reviewer_action(action)
    assert saved is True
