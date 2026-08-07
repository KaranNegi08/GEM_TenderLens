"""
Test Runner for GeM TenderLens.
Executes test cases and logs verification results.
"""

import sys
from utils_logger import get_logger
from tests.test_schemas import (
    test_tender_document_schema,
    test_tender_requirement_schema,
    test_vendor_proposal_schema,
    test_evaluation_finding_schema
)
from tests.test_chunking import test_document_chunker
from tests.test_crew_workflow import test_tender_evaluation_crew_fallback
from tests.test_tender_packages import (
    test_tender_package_discovery,
    test_tender_package_files,
    test_tender_package_processing
)
from tests.test_retrieval import (
    test_chroma_client_manager,
    test_knowledge_retriever,
    test_synthesize_answer
)
from tests.test_mcp_interface import (
    test_mcp_server_tool_definitions,
    test_mcp_client_tool_invocation
)


logger = get_logger("TestRunner")

def run_all_tests():
    print("=" * 60)
    print(" Running GeM TenderLens Verification Test Suite")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    tests = [
        ("Tender Document Schema", test_tender_document_schema),
        ("Tender Requirement Schema", test_tender_requirement_schema),
        ("Vendor Proposal Schema", test_vendor_proposal_schema),
        ("Evaluation Finding Schema", test_evaluation_finding_schema),
        ("Document Chunker", test_document_chunker),
        ("Knowledge Retriever Search", test_knowledge_retriever),
        ("Knowledge Retriever Synthesis", test_synthesize_answer),
        ("Tender Evaluation Crew & Service Pipeline", test_tender_evaluation_crew_fallback),
        ("Tender Package Discovery", test_tender_package_discovery),
        ("Tender Package File Listing", test_tender_package_files),
        ("Tender Package Indexing", test_tender_package_processing),
        ("MCP Server & Tool Definitions", test_mcp_server_tool_definitions),
        ("MCP Client & Function Invocation", test_mcp_client_tool_invocation)
    ]

    
    for name, test_func in tests:
        try:
            test_func()
            print(f" [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f" [FAIL] {name}: {e}")
            logger.exception(f"Test failure in {name}")
            failed += 1
            
    print("=" * 60)
    print(f" Test Results: {passed} PASSED, {failed} FAILED")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
