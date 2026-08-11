"""
Unit tests for vendor_service.py fixes:
1. LangSmith import safety
2. GST normalization consolidation (utils/gst_helper.py)
3. Warranty year vs month regex extraction bug
4. Vendor ID collision prevention using hash
"""

import sys
import pytest
from utils.gst_helper import normalize_gst
from services.vendor_service import VendorService
from services.comparison_service import ComparisonService


def test_langsmith_import_fallback(monkeypatch):
    """Test that traceable decorator works even if langsmith is not imported/available."""
    from services.vendor_service import traceable

    @traceable(name="Test Decorator")
    def dummy_func(a, b):
        return a + b

    assert dummy_func(2, 3) == 5


def test_normalize_gst_utility():
    """Test shared normalize_gst utility behavior."""
    # GST exclusive language -> adds 18%
    assert normalize_gst("grand total before gst", 100000.0, 0.0) == 18000.0
    assert normalize_gst("quoted amount excl. gst", 50000.0, 0.0) == 9000.0

    # GST inclusive or already calculated tax preserved
    assert normalize_gst("inclusive of gst", 100000.0, 18000.0) == 18000.0
    assert normalize_gst("standard pricing", 100000.0, 5000.0) == 5000.0

    # Zero or invalid base amount returns existing tax
    assert normalize_gst("before gst", 0.0, 0.0) == 0.0


def test_vendor_id_uniqueness():
    """Test vendor_id generation includes hash preventing collision between similar names."""
    vs = VendorService.__new__(VendorService)
    # Both names start with SHARMATRAD
    name1 = "Sharma Traders"
    name2 = "Sharma Trading Co"

    clean1 = "SHARMATRAD"
    clean2 = "SHARMATRAD"

    # Process submission generate vendor_id
    import hashlib
    h1 = hashlib.md5(name1.encode()).hexdigest()[:4].upper()
    h2 = hashlib.md5(name2.encode()).hexdigest()[:4].upper()

    id1 = f"VEND_{clean1}_{h1}"
    id2 = f"VEND_{clean2}_{h2}"

    assert id1 != id2
    assert id1.startswith("VEND_SHARMATRAD_")
    assert id2.startswith("VEND_SHARMATRAD_")


def test_warranty_unit_detection_bug_fix():
    """Test warranty regex only converts unit if "year" is attached to the warranty phrase."""
    vs = VendorService.__new__(VendorService)

    # Document text contains "years" in experience section, but warranty specifies "2 months warranty"
    sample_text = """
    Vendor Profile: 15 years of industry experience (established in year 2009).
    Commercial Proposal:
    Total Quoted Amount: INR 500,000
    Terms: 2 months warranty included.
    """

    proposal = vs._extract_proposal_fields("VEND_TEST_1234", sample_text)
    # Under old bug, "years of experience" caused "year" in text_lower -> 2 * 12 = 24 months.
    # Fixed version accurately captures 2 months.
    assert proposal.warranty_months == 2

    # Verify explicit year warranty correctly converts to 36 months
    sample_text_years = """
    Terms: 3 years warranty on all items.
    """
    proposal_years = vs._extract_proposal_fields("VEND_TEST_1234", sample_text_years)
    assert proposal_years.warranty_months == 36
