"""
Custom CrewAI Tools for GeM TenderLens.
Provides vector knowledge base search and document extraction tools.
"""

from typing import Type, Optional
from pydantic import BaseModel, Field
from rag.retriever import KnowledgeRetriever
from utils_logger import get_logger

logger = get_logger(__name__)

class SearchInput(BaseModel):
    """Input schema for search tool."""
    query: str = Field(..., description="Tender requirement or clause search query")
    tender_id: str = Field(..., description="GeM Tender ID string")

class TenderSearchTool:
    """Tool for querying tender knowledge base in ChromaDB."""
    name: str = "search_tender_clause"
    description: str = "Search for specific GeM tender clauses, technical specifications, or BOQ details."

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None):
        self.retriever = retriever or KnowledgeRetriever()

    def run(self, query: str, tender_id: str) -> str:
        """Executes retrieval and formats clause citations."""
        logger.info(f"TenderSearchTool executing query '{query}' for tender '{tender_id}'")
        try:
            results = self.retriever.search_tender_knowledge(tender_id, query, n_results=3)
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

class ProposalExtractorTool:
    """Tool for extracting key financial and technical figures from vendor documents."""
    name: str = "extract_proposal_fields"
    description: str = "Extracts vendor quoted price, delivery days, warranty, and technical claims."

    def run(self, text_content: str) -> str:
        """Rule-based and structured pattern parsing tool."""
        logger.info("Executing ProposalExtractorTool on vendor text.")
        try:
            import re
            prices = re.findall(r'(?:rs\.?|inr|\u20b9|total|price|quote)[:\s]*([0-9,]+(?:\.[0-9]{2})?)', text_content, re.IGNORECASE)
            days = re.findall(r'(\d+)\s*(?:days|weeks|working days)', text_content, re.IGNORECASE)
            warranty = re.findall(r'(\d+)\s*(?:months|years)\s*warranty', text_content, re.IGNORECASE)

            quoted_amount = prices[0] if prices else "Not explicitly specified"
            delivery = days[0] if days else "Not specified"
            warr = warranty[0] if warranty else "Standard"

            return (
                f"Quoted Amount: INR {quoted_amount}\n"
                f"Delivery Days: {delivery}\n"
                f"Warranty: {warr}\n"
                f"Text Excerpt: {text_content[:300]}..."
            )
        except Exception as e:
            logger.exception(f"Error in ProposalExtractorTool: {e}")
            return f"Extraction failed: {str(e)}"
