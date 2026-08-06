"""
Unit tests for Document Chunking logic in GeM TenderLens.
"""

from rag.chunking import DocumentChunker

def test_document_chunker():
    doc_data = {
        "filename": "GeM_Bid_GEM_2026_B_7798305.txt",
        "ext": ".txt",
        "pages": [
            {
                "page_number": 1,
                "content": "Mandatory Requirement: Delivery period must be 21 days to Kupwara.\n\nExperience Criteria: Minimum 2 years experience.",
                "is_scanned": False
            }
        ]
    }
    
    chunks = DocumentChunker.chunk_document(
        doc_data=doc_data,
        tender_id="GEM/2026/B/7798305",
        document_id="DOC_TEST",
        document_type="bid_document"
    )
    
    assert len(chunks) > 0
    assert chunks[0].tender_id == "GEM/2026/B/7798305"
    assert chunks[0].mandatory_flag is True
    assert chunks[0].source_file == "GeM_Bid_GEM_2026_B_7798305.txt"
