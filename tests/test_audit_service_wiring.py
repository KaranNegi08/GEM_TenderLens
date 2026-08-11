"""
Unit tests for DatabaseAuditService wiring across TenderService, VendorService, TenderEvaluationCrew, and ReviewerAction retrieval.
"""

import pytest
from schemas.audit import ReviewerAction, AuditLog
from services.audit_service import DatabaseAuditService
from services.tender_service import TenderService
from services.vendor_service import VendorService
from crew.tender_crew import TenderEvaluationCrew


def test_get_reviewer_actions_filtering():
    """Test saving and retrieving reviewer actions filtered by finding_id."""
    finding_1 = "FINDING_TEST_001"
    finding_2 = "FINDING_TEST_002"

    act1 = ReviewerAction(
        finding_id=finding_1,
        action="APPROVED",
        reviewer_comments="Spec verified by committee."
    )
    act2 = ReviewerAction(
        finding_id=finding_2,
        action="REJECTED",
        reviewer_comments="Missing ISO certificate."
    )

    DatabaseAuditService.save_reviewer_action(act1)
    DatabaseAuditService.save_reviewer_action(act2)

    # Fetch filtered by finding_1
    res1 = DatabaseAuditService.get_reviewer_actions(finding_id=finding_1)
    assert len(res1) >= 1
    assert res1[0]["finding_id"] == finding_1
    assert res1[0]["action"] == "APPROVED"

    # Fetch all recent reviewer actions
    all_res = DatabaseAuditService.get_reviewer_actions(limit=10)
    assert len(all_res) >= 2


def test_audit_logs_population():
    """Test saving audit logs and retrieving them via get_recent_audit_logs."""
    import uuid
    log_id = f"AUDIT_TEST_{uuid.uuid4().hex[:8].upper()}"

    log = AuditLog(
        log_id=log_id,
        actor="TestRunner",
        action_type="UNIT_TEST_ACTION",
        details={"test_key": "test_value"}
    )
    saved = DatabaseAuditService.save_audit_log(log)
    assert saved is True

    recent = DatabaseAuditService.get_recent_audit_logs(limit=20)
    matching = [l for l in recent if l["log_id"] == log_id]
    assert len(matching) == 1
    assert matching[0]["actor"] == "TestRunner"
    assert matching[0]["action_type"] == "UNIT_TEST_ACTION"
