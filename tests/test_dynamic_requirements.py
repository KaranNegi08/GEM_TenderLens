"""
Unit tests for dynamic tender requirements persistence and generic compliance evaluator.
"""

import pytest
from schemas.tender import TenderRequirement
from services.tender_service import TenderService
from services.comparison_service import ComparisonService
from utils.evaluator_helper import evaluate_generic_requirement


def test_requirements_db_persistence():
    """Test saving and retrieving dynamic TenderRequirements via SQLite DB."""
    tender_id = "GEM/2026/B/SOLAR_TEST_001"

    reqs = [
        TenderRequirement(
            requirement_id="REQ_SOLAR_01",
            tender_id=tender_id,
            clause_id="CLAUSE_4.1",
            requirement_text="Solar Panel 500W Monocrystalline PERC Tier 1 Efficiency",
            requirement_type="technical",
            is_mandatory=True,
            evidence_required="datasheet",
            page_number=4
        ),
        TenderRequirement(
            requirement_id="REQ_SOLAR_02",
            tender_id=tender_id,
            clause_id="CLAUSE_5.2",
            requirement_text="Delivery Timeline <= 15 days to site location",
            requirement_type="delivery",
            is_mandatory=True,
            evidence_required="undertaking",
            page_number=7
        )
    ]

    saved = TenderService.save_requirements_to_db(tender_id, reqs)
    assert saved is True

    fetched = TenderService.get_stored_requirements(tender_id)
    assert len(fetched) == 2
    assert fetched[0]["requirement_id"] == "REQ_SOLAR_01"
    assert fetched[0]["clause_id"] == "CLAUSE_4.1"
    assert fetched[1]["requirement_id"] == "REQ_SOLAR_02"


def test_evaluate_generic_requirement_helper():
    """Test generic evaluator with delivery, warranty, and custom technical requirements."""
    # Test 1: Delivery requirement
    req_delivery = {
        "requirement_id": "REQ_DELIV_15",
        "requirement_name": "Delivery within 15 days",
        "requirement_text": "Delivery period maximum 15 days to destination."
    }
    proposal_fast = {"delivery_days": 10}
    status, exp, conf = evaluate_generic_requirement(req_delivery, "delivery lead time 10 days", proposal_fast)
    assert status == "compliant"
    assert "10 days" in exp

    proposal_slow = {"delivery_days": 25}
    status, exp, conf = evaluate_generic_requirement(req_delivery, "delivery 25 days", proposal_slow)
    assert status == "non_compliant"

    # Test 2: Warranty requirement
    req_warranty = {
        "requirement_id": "REQ_WAR_36",
        "requirement_name": "3-Year Onsite Warranty",
        "requirement_text": "Equipment must carry 3-yr onsite comprehensive warranty."
    }
    proposal_war_good = {"warranty_months": 36}
    status, exp, conf = evaluate_generic_requirement(req_warranty, "36 months warranty", proposal_war_good)
    assert status == "compliant"

    proposal_war_bad = {"warranty_months": 12}
    status, exp, conf = evaluate_generic_requirement(req_warranty, "12 months warranty", proposal_war_bad)
    assert status == "non_compliant"


def test_comparison_service_dynamic_tender():
    """Test ComparisonService using stored DB requirements for a new custom tender type."""
    tender_id = "GEM/2026/B/MED_EQUIP_55"

    # Save dynamic requirements for medical equipment tender
    reqs = [
        TenderRequirement(
            requirement_id="REQ_MED_01",
            tender_id=tender_id,
            clause_id="SEC_2",
            requirement_text="Patient Monitor: 12-inch Touch Display, ECG, SpO2, NIBP",
            requirement_type="technical",
            is_mandatory=True,
            page_number=2
        ),
        TenderRequirement(
            requirement_id="REQ_MED_02",
            tender_id=tender_id,
            clause_id="SEC_5",
            requirement_text="ISO 9001 Quality Certification required",
            requirement_type="eligibility",
            is_mandatory=True,
            page_number=5
        )
    ]
    TenderService.save_requirements_to_db(tender_id, reqs)

    cs = ComparisonService()
    dossiers = [
        {
            "vendor_id": "VEND_MED_01",
            "vendor_name": "MedTech Solutions",
            "proposal": {
                "quoted_amount": 250000.0,
                "tax_amount": 45000.0,
                "delivery_days": 14,
                "warranty_months": 24,
                "certificates_submitted": ["ISO 9001 Quality Certificate"]
            },
            "full_text": "medtech proposal for patient monitor 12-inch touch display ecg spo2 nibp. iso 9001 certificate attached."
        }
    ]

    res = cs.generate_comparison_matrix(tender_id, dossiers)
    assert res["tender_id"] == tender_id
    assert len(res["compliance_findings"]) == 2

    r1_finding = [f for f in res["compliance_findings"] if f["requirement_id"] == "REQ_MED_01"][0]
    assert r1_finding["status"] == "compliant"

    r2_finding = [f for f in res["compliance_findings"] if f["requirement_id"] == "REQ_MED_02"][0]
    assert r2_finding["status"] == "compliant"
