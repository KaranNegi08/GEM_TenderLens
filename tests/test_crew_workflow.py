"""
Integration tests for CrewAI workflow and service fallback pipeline.
"""

from crew.tender_crew import TenderEvaluationCrew
from services.vendor_service import VendorService

def test_tender_evaluation_crew_fallback():
    # Ingest sample vendor proposal
    vendor_service = VendorService()
    v_res = vendor_service.process_vendor_submission(
        vendor_name="Test Publisher",
        tender_id="GEM/2026/B/7798305",
        file_paths=["./data/uploads/vendor_submissions/Vendor_Apex_Publishers/proposal_apex_publishers.eml"]
    )
    
    assert v_res["success"] is True
    
    crew_runner = TenderEvaluationCrew("GEM/2026/B/7798305")
    res = crew_runner.run_full_evaluation(
        document_list=["GeM_Bid_GEM_2026_B_7798305.txt"],
        vendor_dossiers=[v_res]
    )
    
    assert res["tender_id"] == "GEM/2026/B/7798305"
    assert res["total_vendors"] == 1
    assert len(res["commercial_comparison"]) == 1
    assert len(res["compliance_findings"]) > 0
