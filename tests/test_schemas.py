from datetime import date
from schemas.tender import TenderDocument, TenderRequirement
from schemas.vendor import VendorSubmission, VendorProposal
from schemas.evaluation import EvidenceCitation, EvaluationFinding

def test_tender_document_schema():
    doc = TenderDocument(
        tender_id="GEM/2026/B/7798305",
        document_id="DOC_001",
        document_type="bid_document",
        document_version="1.0",
        source_file="GeM_Bid_GEM_2026_B_7798305.pdf",
        is_governing_document=True
    )
    assert doc.tender_id == "GEM/2026/B/7798305"
    assert doc.document_type == "bid_document"

def test_tender_requirement_schema():
    req = TenderRequirement(
        requirement_id="REQ_001",
        tender_id="GEM/2026/B/7798305",
        clause_id="CLAUSE_5",
        requirement_text="Experience Criteria: 2 Years",
        requirement_type="eligibility",
        is_mandatory=True,
        page_number=2
    )
    assert req.is_mandatory is True
    assert req.page_number == 2

def test_vendor_proposal_schema():
    prop = VendorProposal(
        vendor_id="VEND_001",
        quoted_amount=71400.0,
        currency="INR",
        tax_amount=3400.0,
        delivery_days=14,
        warranty_months=12,
        extraction_confidence=0.95
    )
    assert prop.quoted_amount == 71400.0
    assert prop.delivery_days == 14

def test_evaluation_finding_schema():
    cit_t = EvidenceCitation(source_file="GeM_Bid.pdf", page_number=1, excerpt="Mandatory delivery: 21 days")
    cit_v = EvidenceCitation(source_file="Proposal.pdf", page_number=1, excerpt="Offered delivery: 14 days")
    
    finding = EvaluationFinding(
        vendor_id="VEND_001",
        requirement_id="REQ_002",
        status="compliant",
        explanation="Offered delivery 14 days meets limit.",
        tender_evidence=cit_t,
        vendor_evidence=cit_v,
        confidence=0.95
    )
    assert finding.status == "compliant"
    assert finding.reviewer_status == "pending"
