"""
Unit tests for export_service.py fixes:
1. PDF Report Export via ReportLab
2. Commercial Tax Note formatting
3. L-1 Financial vs Technically-Qualified Header
4. Status badges mapping & unknown fallback
5. True Markdown HTML rendering
"""

import os
import pytest
from services.export_service import ExportService


def test_export_service_all_formats_including_pdf(tmp_path):
    """Test export service generates .md, .html, .json, and .pdf files."""
    es = ExportService()
    es.export_dir = str(tmp_path)

    tender_id = "GEM/2026/B/TEST_EXPORT_123"
    matrix = {
        "tender_id": tender_id,
        "total_vendors": 2,
        "l1_vendor": "Alpha Tech",
        "l1_cost": 100000.0,
        "l1_qualified_vendor": "Beta Systems",
        "l1_qualified_cost": 110000.0,
        "l1_deviations_count": 1,
        "commercial_comparison": [
            {
                "rank": 1,
                "vendor_name": "Alpha Tech",
                "base_price": 100000.0,
                "tax_amount": 18000.0,
                "tax_note": "₹18,000.00 (18% GST Added)",
                "total_cost": 118000.0,
                "delivery_days": 15,
                "mse_status": "Yes",
                "l_status": "L-1"
            }
        ],
        "compliance_findings": [
            {
                "vendor_name": "Alpha Tech",
                "requirement_name": "ISO Certification",
                "status": "non_compliant",
                "explanation": "Missing ISO certificate",
                "confidence": 0.95
            },
            {
                "vendor_name": "Alpha Tech",
                "requirement_name": "Custom Spec",
                "status": "unknown_future_status",
                "explanation": "Custom evaluation",
                "confidence": 0.80
            }
        ],
        "risk_queue": [
            {
                "vendor_name": "Alpha Tech",
                "issue_type": "NON_COMPLIANT",
                "description": "Missing ISO cert",
                "suggested_action": "Request document"
            }
        ]
    }

    result = es.generate_committee_report(tender_id, matrix, reviewer_notes="Approved with warning")

    assert "markdown" in result
    assert "html" in result
    assert "json" in result
    assert "pdf" in result

    assert os.path.exists(result["markdown"])
    assert os.path.exists(result["html"])
    assert os.path.exists(result["json"])
    assert result["pdf"] is not None and os.path.exists(result["pdf"])

    # Issue #3 Verification: Header contains both Financial L-1 & Technically-Qualified L-1
    with open(result["markdown"], "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "**Financial L-1 Vendor:** `Alpha Tech`" in md_text
    assert "**Technically-Qualified L-1 Vendor:** `Beta Systems`" in md_text
    assert "Financial L-1 vendor has 1 compliance deviation(s)" in md_text

    # Issue #2 Verification: Uses tax_note directly
    assert "₹18,000.00 (18% GST Added)" in md_text

    # Issue #4 Verification: Explicit non_compliant badge & unknown fallback
    assert "🔴 NON-COMPLIANT" in md_text
    assert "⚪ UNKNOWN STATUS" in md_text

    # Issue #5 Verification: HTML contains <table> tag instead of raw <pre>
    with open(result["html"], "r", encoding="utf-8") as f:
        html_text = f.read()

    assert '<div class="report-content">' in html_text
    assert '<table>' in html_text
    assert '<th>Rank</th>' in html_text
