"""
Evaluation & Citation schemas for GeM TenderLens.
Defines models for traceable evidence citations and compliance findings.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from utils_logger import get_logger

logger = get_logger(__name__)

class EvidenceCitation(BaseModel):
    """Pinpoints source document evidence with file and page location."""
    source_file: str = Field(..., description="Source document filename")
    page_number: Optional[int] = Field(default=None, description="Page number where evidence appears")
    clause_id: Optional[str] = Field(default=None, description="Clause or section identifier")
    excerpt: str = Field(..., description="Exact textual excerpt supporting finding")


class EvaluationFinding(BaseModel):
    """Detailed compliance evaluation result for a vendor against a tender requirement."""
    vendor_id: str = Field(..., description="Vendor ID under review")
    requirement_id: str = Field(..., description="Target requirement ID")
    status: Literal["compliant", "partial", "non_compliant", "review_required"] = Field(
        ..., description="Compliance status"
    )
    explanation: str = Field(..., description="Clear rationale explaining the status determination")
    tender_evidence: EvidenceCitation = Field(..., description="Citation from official tender document")
    vendor_evidence: Optional[EvidenceCitation] = Field(default=None, description="Citation from vendor proposal")
    confidence: float = Field(default=1.0, description="AI model confidence score (0.0 to 1.0)")
    reviewer_status: Literal["pending", "approved", "rejected", "clarification_needed"] = Field(
        default="pending", description="Status set by human reviewer"
    )

   
