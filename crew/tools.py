"""
Custom CrewAI Tools for GeM TenderLens.
Provides vector knowledge base search and document extraction tools as CrewAI BaseTool subclasses.
"""

from typing import Type, Optional, Any
from pydantic import BaseModel, Field, PrivateAttr
from rag.retriever import KnowledgeRetriever
from utils.proposal_extractor import extract_proposal_fields_from_text
from utils_logger import get_logger

logger = get_logger(__name__)

try:
    from crewai.tools import BaseTool
except ImportError:
    class BaseTool:
        name: str = ""
        description: str = ""
        args_schema: Any = None
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def run(self, *args, **kwargs):
            return self._run(*args, **kwargs)


class SearchInput(BaseModel):
    """Input schema for search tool."""
    query: str = Field(..., description="Tender requirement or clause search query")
    tender_id: str = Field(..., description="GeM Tender ID string")


class TenderSearchTool(BaseTool):
    """Tool for querying tender knowledge base in ChromaDB."""
    name: str = "search_tender_clause"
    description: str = "Search for specific GeM tender clauses, technical specifications, or BOQ details."
    args_schema: Type[BaseModel] = SearchInput
    _retriever: Any = PrivateAttr(default=None)

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None, **kwargs):
        super().__init__(**kwargs)
        self._retriever = retriever or KnowledgeRetriever()

    def _run(self, query: str, tender_id: str) -> str:
        """Executes retrieval and formats clause citations."""
        logger.info(f"TenderSearchTool executing query '{query}' for tender '{tender_id}'")
        try:
            results = self._retriever.search_tender_knowledge(tender_id, query, n_results=3)
            if not results:
                return "No matching tender clauses found in ChromaDB."

            formatted = []
            for r in results:
                meta = r["metadata"]
                formatted.append(
                    f"[Source: {meta.get('source_file')}, Page: {meta.get('page_number')}, Clause: {meta.get('clause_id')}]\n"
                    f"{r['text']}"
                )
            return "\n\n---\n\n".join(formatted)
        except Exception as e:
            logger.exception(f"Error in TenderSearchTool: {e}")
            return f"Error executing tender search: {str(e)}"


class ExtractionInput(BaseModel):
    """Input schema for vendor proposal extraction tool."""
    text_content: str = Field(..., description="Text content from vendor proposal document")


class ProposalExtractorTool(BaseTool):
    """Tool for extracting key financial and technical figures from vendor documents."""
    name: str = "extract_proposal_fields"
    description: str = "Extracts vendor quoted price, delivery days, warranty, and technical claims."
    args_schema: Type[BaseModel] = ExtractionInput

    def _run(self, text_content: str) -> str:
        """Rule-based structured pattern parsing tool using consolidated proposal_extractor utility."""
        logger.info("Executing ProposalExtractorTool on vendor text.")
        try:
            proposal = extract_proposal_fields_from_text(vendor_id="VENDOR_EXTRACT", text=text_content)
            quoted_str = f"INR {proposal.quoted_amount:,.2f}" if proposal.quoted_amount else "Not explicitly specified"
            tax_str = f"INR {proposal.tax_amount:,.2f}" if proposal.tax_amount else "0.00"

            return (
                f"Quoted Amount: {quoted_str}\n"
                f"Tax / GST Amount: {tax_str}\n"
                f"Delivery Days: {proposal.delivery_days}\n"
                f"Warranty Months: {proposal.warranty_months}\n"
                f"Certificates Submitted: {', '.join(proposal.certificates_submitted) if proposal.certificates_submitted else 'None'}\n"
                f"Technical Claims: {', '.join(proposal.technical_claims) if proposal.technical_claims else 'None'}\n"
                f"Text Excerpt: {text_content[:300]}..."
            )
        except Exception as e:
            logger.exception(f"Error in ProposalExtractorTool: {e}")
            return f"Extraction failed: {str(e)}"
