"""
Unit tests for CrewAI tools and agent tool wiring.
"""

import pytest
from crew.tools import TenderSearchTool, ProposalExtractorTool
from crew.agents import TenderAgents
from utils.proposal_extractor import extract_proposal_fields_from_text


def test_proposal_extractor_tool_standalone():
    """Test ProposalExtractorTool standalone execution and output format."""
    tool = ProposalExtractorTool()

    sample_text = """
    Commercial Bid:
    Quoted Total Price: INR 250,000.00
    Tax: +18% GST extra
    Delivery Timeline: 14 days to site.
    Warranty: 3 years comprehensive warranty.
    Certificates Attached: ISO 9001 Quality Certificate, Udyam Registration.
    """

    res = tool.run(text_content=sample_text)
    assert "Quoted Amount: INR 250,000.00" in res
    assert "Delivery Days: 14" in res
    assert "Warranty Months: 36" in res
    assert "ISO 9001 Quality Certificate" in res


def test_tender_search_tool_standalone():
    """Test TenderSearchTool standalone execution without crashing."""
    mock_retriever = type("MockRetriever", (), {
        "search_tender_knowledge": lambda self, tid, q, n_results=3: [
            {"metadata": {"source_file": "bid.pdf", "page_number": 1, "clause_id": "TS-01"}, "text": "Core i5 laptop specification."}
        ]
    })()

    search_tool = TenderSearchTool(retriever=mock_retriever)
    out = search_tool.run(query="laptop specification", tender_id="TENDER_001")
    assert "[Source: bid.pdf, Page: 1, Clause: TS-01]" in out
    assert "Core i5 laptop specification." in out


def test_tender_agents_tools_wiring():
    """Test that TenderAgents correctly assigns search and extractor tools to specialized agents."""
    ta = TenderAgents()

    tech_agent = ta.technical_compliance_agent()
    assert hasattr(tech_agent, "tools")
    assert len(tech_agent.tools) == 2

    writer_agent = ta.evaluation_writer_agent()
    assert getattr(writer_agent, "tools", None) is None or len(getattr(writer_agent, "tools", [])) == 0
