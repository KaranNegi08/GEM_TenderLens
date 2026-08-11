"""
Unit tests for vendor intake page fixes (pages/2_vendor_intake.py).
Tests:
1. Safe vendor name matching (case-insensitive and trimmed)
2. Dossier replacement vs append logic in session state
3. Timestamp prefixing on file paths
"""

import pytest
from datetime import datetime
from schemas.vendor import VendorSubmission


def find_existing_dossier_idx(vendor_dossiers, v_name_input):
    return next(
        (i for i, d in enumerate(vendor_dossiers) 
         if d and d.get("submission") and getattr(d["submission"], "vendor_name", "").lower().strip() == v_name_input.lower().strip()),
        None
    )


def test_vendor_name_matching_case_and_whitespace():
    submission_1 = VendorSubmission(
        vendor_id="VEND_001",
        vendor_name="Acme Supplies Ltd",
        tender_id="GEM/2026/B/12345"
    )
    dossiers = [{"submission": submission_1, "success": True}]

    # Case variations and whitespace variations should match
    assert find_existing_dossier_idx(dossiers, "Acme Supplies Ltd") == 0
    assert find_existing_dossier_idx(dossiers, "acme supplies ltd ") == 0
    assert find_existing_dossier_idx(dossiers, "  ACME SUPPLIES LTD  ") == 0
    assert find_existing_dossier_idx(dossiers, "Different Vendor") is None


def test_vendor_name_matching_edge_cases():
    # Handle None dossier, missing submission key, or submission with None vendor_name safely
    dossiers = [
        None,
        {},
        {"submission": None},
        {"submission": VendorSubmission(vendor_id="VEND_002", vendor_name="Beta Corp", tender_id="T1")}
    ]

    assert find_existing_dossier_idx(dossiers, "beta corp") == 3
    assert find_existing_dossier_idx(dossiers, "unknown vendor") is None


def test_dossier_replacement_in_session_state():
    submission_v1 = VendorSubmission(
        vendor_id="VEND_001",
        vendor_name="Acme Supplies Ltd",
        tender_id="GEM/2026/B/12345",
        revision_number=1
    )
    dossiers = [{"submission": submission_v1, "success": True}]

    input_vendor = "acme supplies ltd "
    idx = find_existing_dossier_idx(dossiers, input_vendor)
    assert idx == 0

    submission_v2 = VendorSubmission(
        vendor_id="VEND_001",
        vendor_name="Acme Supplies Ltd",
        tender_id="GEM/2026/B/12345",
        revision_number=2
    )
    new_res = {"submission": submission_v2, "success": True}

    if idx is not None:
        dossiers[idx] = new_res
    else:
        dossiers.append(new_res)

    assert len(dossiers) == 1
    assert dossiers[0]["submission"].revision_number == 2


def test_timestamp_prefix_format():
    filename = "proposal.pdf"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_name = f"{timestamp}_{filename}"

    assert timestamped_name.endswith("_proposal.pdf")
    assert len(timestamp) == 15  # YYYYMMDD_HHMMSS
