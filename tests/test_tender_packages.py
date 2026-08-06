"""
Unit test for folder-based tender package discovery and indexing.
"""

from services.tender_service import TenderService

def test_tender_package_discovery():
    service = TenderService()
    tenders = service.list_available_tenders()
    assert len(tenders) > 0, "Expected at least 1 tender package folder in data/uploads/tender_documents"
    assert "GEM_9146015" in tenders, "Expected GEM_9146015 tender package folder"

def test_tender_package_files():
    service = TenderService()
    files = service.get_tender_files("GEM_9146015")
    assert len(files) >= 2, f"Expected at least 2 files in GEM_9146015 package, got {len(files)}"

def test_tender_package_processing():
    service = TenderService()
    res = service.process_tender_package("GEM_9146015")
    assert res["success"] is True, f"Failed to process tender package: {res}"
    assert res["total_files"] >= 2
    assert res["total_chunks"] > 0

if __name__ == "__main__":
    test_tender_package_discovery()
    test_tender_package_files()
    test_tender_package_processing()
    print("All tender package tests passed!")
