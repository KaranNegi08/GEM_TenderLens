"""
Unit tests for centralized text cleaning in DocumentLoader.load_document().
"""

import os
import tempfile
import pytest
from rag.document_loader import DocumentLoader


def test_centralized_text_cleaning_txt():
    """Verify that TXT file with Hindi/Devanagari text and noise is cleaned centrally."""
    sample_text = "Vendor Offer Details\nयह एक हिंदी पाठ है\nSpecial terms & conditions / warranty."
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(sample_text)
        temp_path = f.name

    try:
        doc = DocumentLoader.load_document(temp_path)
        assert doc["error"] is None
        assert len(doc["pages"]) == 1
        cleaned_content = doc["pages"][0]["content"]
        
        # Devanagari text should be stripped
        assert "यह" not in cleaned_content
        assert "हिंदी" not in cleaned_content
        # English content preserved
        assert "Vendor Offer Details" in cleaned_content
        assert "Special terms" in cleaned_content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_clean_english_text_idempotence():
    """Verify clean_english_text is idempotent."""
    raw = "Header text\nहिंदी पाठ\nOrphan slash / test `symbol`"
    pass1 = DocumentLoader.clean_english_text(raw)
    pass2 = DocumentLoader.clean_english_text(pass1)
    
    assert pass1 == pass2
