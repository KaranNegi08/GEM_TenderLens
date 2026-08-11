"""
Unit tests for ValidationService wiring in VendorService and TenderService.
"""

import os
import pytest
from services.validation_service import ValidationService
from services.vendor_service import VendorService
from services.tender_service import TenderService


def test_validation_service_with_and_without_doc_data(tmp_path):
    """Test validate_file_accessibility works both with and without pre-loaded doc_data."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Sample text document content for testing.", encoding="utf-8")
    fp = str(test_file)

    # Call without pre-loaded doc_data
    res1 = ValidationService.validate_file_accessibility(fp)
    assert res1["filename"] == "sample.txt"
    assert res1["is_valid_text"] is True
    assert res1["is_scanned"] is False
    assert res1["scanned_pages"] == []

    # Call with pre-loaded doc_data (performance optimization)
    mock_doc_data = {
        "is_scanned": True,
        "pages": [{"page_number": 1, "is_scanned": True, "content": ""}]
    }
    res2 = ValidationService.validate_file_accessibility(fp, doc_data=mock_doc_data)
    assert res2["is_scanned"] is True
    assert res2["scanned_pages"] == [1]
    assert res2["is_valid_text"] is False
    assert "MANUAL REVIEW REQUIRED" in res2["message"]


def test_vendor_service_uses_validation(tmp_path):
    """Test VendorService uses ValidationService and sets scanned flags correctly."""
    vs = VendorService.__new__(VendorService)

    test_file = tmp_path / "proposal.txt"
    test_file.write_text("Total Amount: INR 500,000. Delivery in 10 days.", encoding="utf-8")
    fp = str(test_file)

    res = vs._extract_proposal_fields("VEND_TEST", test_file.read_text())
    assert res.quoted_amount == 500000.0


def test_tender_service_returns_scanned_pages(tmp_path):
    """Test TenderService includes scanned_pages in process_tender_file output."""
    ts = TenderService.__new__(TenderService)
    ts.storage_dir = str(tmp_path)
    ts.chroma_manager = type("MockChroma", (), {"get_or_create_collection": lambda *a, **k: type("MockCol", (), {"upsert": lambda *a, **k: None})()})()
    ts.embedding_provider = type("MockEmbed", (), {"embed_texts": lambda self, t: [[0.1]*384 for _ in t]})()

    test_file = tmp_path / "tender_spec.txt"
    test_file.write_text("Technical specification: Core i5 Laptop. Delivery 15 days.", encoding="utf-8")
    fp = str(test_file)

    out = ts.process_tender_file(fp, "TENDER_001")
    assert out["success"] is True
    assert "is_scanned" in out
    assert "scanned_pages" in out
    assert out["is_scanned"] is False
    assert out["scanned_pages"] == []
