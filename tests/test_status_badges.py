"""
Unit tests for utils/status_badges.py shared helper module.
"""

import pytest
from utils.status_badges import get_status_badge, STATUS_BADGES


def test_status_badges_dictionary():
    assert STATUS_BADGES["compliant"] == "🟢 Compliant"
    assert STATUS_BADGES["review_required"] == "🟡 Review Required"
    assert STATUS_BADGES["partial"] == "🔵 Partial / Exemption"
    assert STATUS_BADGES["non_compliant"] == "🔴 Non-Compliant"


def test_get_status_badge_standard():
    assert get_status_badge("compliant") == "🟢 Compliant"
    assert get_status_badge("review_required") == "🟡 Review Required"
    assert get_status_badge("partial") == "🔵 Partial / Exemption"
    assert get_status_badge("non_compliant") == "🔴 Non-Compliant"
    assert get_status_badge("unknown_status") == "⚪ Unknown Status"


def test_get_status_badge_uppercase():
    assert get_status_badge("compliant", upper=True) == "🟢 COMPLIANT"
    assert get_status_badge("review_required", upper=True) == "🟡 REVIEW REQUIRED"
    assert get_status_badge("partial", upper=True) == "🔵 PARTIAL / EXEMPTION"
    assert get_status_badge("non_compliant", upper=True) == "🔴 NON-COMPLIANT"
    assert get_status_badge("invalid_key", upper=True) == "⚪ UNKNOWN STATUS"
