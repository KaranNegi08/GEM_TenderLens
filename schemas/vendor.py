"""
Vendor submission schemas for GeM TenderLens.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from utils_logger import get_logger

logger = get_logger(__name__)

class VendorSubmission(BaseModel):
    """Represents a vendor proposal intake email or dossier submission."""
    vendor_id: str = Field(..., description="Unique vendor ID e.g. VEND_001")
    vendor_name: str = Field(..., description="Company or supplier name")
    tender_id: str = Field(..., description="Target tender ID")
    email_subject: Optional[str] = Field(default=None, description="Email subject line if received via email")
    received_at: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp of submission")
    revision_number: int = Field(default=1, description="Version number of vendor submission")
    attachment_paths: List[str] = Field(default_factory=list, description="List of attached document paths")

    def __init__(self, **data):
        try:
            super().__init__(**data)
            logger.debug(f"Initialized VendorSubmission: {self.vendor_name} ({self.vendor_id})")
        except Exception as e:
            logger.error(f"Failed to instantiate VendorSubmission: {e}")
            raise

class VendorProposal(BaseModel):
    """Structured extraction of vendor pricing, delivery, and compliance details."""
    vendor_id: str = Field(..., description="Unique vendor ID")
    quoted_amount: Optional[float] = Field(default=None, description="Total quoted price before tax")
    currency: str = Field(default="INR", description="Currency code")
    tax_amount: Optional[float] = Field(default=0.0, description="Applicable tax amount")
    delivery_days: Optional[int] = Field(default=None, description="Offered delivery time in days")
    warranty_months: Optional[int] = Field(default=None, description="Offered warranty in months")
    technical_claims: List[str] = Field(default_factory=list, description="Summary of key technical compliance claims")
    certificates_submitted: List[str] = Field(default_factory=list, description="List of submitted compliance certificates")
    extraction_confidence: float = Field(default=1.0, description="Confidence score from AI extraction (0.0 to 1.0)")

    def __init__(self, **data):
        try:
            super().__init__(**data)
            logger.debug(f"Initialized VendorProposal: {self.vendor_id} - amount={self.quoted_amount}")
        except Exception as e:
            logger.error(f"Failed to instantiate VendorProposal: {e}")
            raise
