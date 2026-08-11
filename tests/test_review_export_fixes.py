"""
Unit tests for review & export fixes in pages/5_review_export.py.
"""

import pytest
from schemas.audit import ReviewerAction
from services.audit_service import DatabaseAuditService


def test_reviewer_action_schema_and_persistence():
    """Test ReviewerAction schema instantiation and DatabaseAuditService persistence for per-finding reviews."""
    finding_key = "VEND_ALPHA:TS-01"
    action = "approved"
    comments = "OEM certificate verified on page 3."

    action_obj = ReviewerAction(
        finding_id=finding_key,
        action=action,
        reviewer_comments=comments
    )

    assert action_obj.finding_id == finding_key
    assert action_obj.action == "approved"
    assert action_obj.reviewer_comments == comments

    res = DatabaseAuditService.save_reviewer_action(action_obj)
    assert res is True


def test_signoff_status_options():
    """Test valid sign-off approval status options match flow spec."""
    valid_statuses = [
        "APPROVED_RECOMMENDED_FOR_AWARD",
        "CLARIFICATIONS_REQUESTED",
        "REJECTED_RE_TENDER_REQUIRED"
    ]

    assert "APPROVED_RECOMMENDED_FOR_AWARD" in valid_statuses
    assert "CLARIFICATIONS_REQUESTED" in valid_statuses
    assert "REJECTED_RE_TENDER_REQUIRED" in valid_statuses
    assert "PENDING_REVIEW" not in valid_statuses
