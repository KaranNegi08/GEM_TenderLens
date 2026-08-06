"""
Tender schemas for GeM TenderLens.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from utils_logger import get_logger

logger = get_logger(__name__)

class TenderDocument(BaseModel):
    """Represents a governing tender or bid document metadata."""
    tender_id: str = Field(..., description="Unique GeM tender ID e.g. GEM/2026/B/7798305")
    document_id: str = Field(..., description="Unique identifier for the document")
    document_type: str = Field(..., description="Type of doc: bid_document, boq, technical_spec, corrigendum")
    document_version: str = Field(default="1.0", description="Version string")
    source_file: str = Field(..., description="Original filename or path")
    effective_date: Optional[date] = Field(default=None, description="Date document became effective")
    is_governing_document: bool = Field(default=True, description="Whether this is currently active baseline document")

    def __init__(self, **data):
        try:
            super().__init__(**data)
            logger.debug(f"Initialized TenderDocument: {self.tender_id} - {self.document_id}")
        except Exception as e:
            logger.error(f"Failed to instantiate TenderDocument: {e}")
            raise

class TenderRequirement(BaseModel):
    """Represents a specific mandatory or evaluated tender requirement."""
    requirement_id: str = Field(..., description="Unique requirement ID")
    tender_id: str = Field(..., description="Associated tender ID")
    clause_id: Optional[str] = Field(default=None, description="Clause or section reference number")
    requirement_text: str = Field(..., description="Detailed description of mandatory requirement")
    requirement_type: str = Field(default="technical", description="technical, commercial, eligibility, delivery")
    is_mandatory: bool = Field(default=True, description="Whether compliance is strictly required")
    evidence_required: Optional[str] = Field(default=None, description="Type of proof required e.g. certificate, invoice")
    page_number: Optional[int] = Field(default=None, description="Source page number in tender PDF")

    def __init__(self, **data):
        try:
            super().__init__(**data)
            logger.debug(f"Initialized TenderRequirement: {self.requirement_id}")
        except Exception as e:
            logger.error(f"Failed to instantiate TenderRequirement: {e}")
            raise
