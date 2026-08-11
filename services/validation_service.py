"""
Validation Service for GeM TenderLens.
Enforces guardrails: checks scanned PDFs, validates Pydantic schemas, and flags low-confidence extractions.
"""

import os
from typing import Dict, Any, List, Optional
from rag.document_loader import DocumentLoader
from utils_logger import get_logger

logger = get_logger(__name__)

class ValidationService:
    """Provides validation and guardrail checks across files and proposal objects."""

    @staticmethod
    def validate_file_accessibility(file_path: str, doc_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Inspects file for text accessibility. Flags scanned documents as manual review required.
        Accepts optional pre-loaded doc_data to avoid duplicate document parsing.
        """
        logger.info(f"Validating text accessibility for file: {file_path}")
        try:
            if doc_data is None:
                doc_data = DocumentLoader.load_document(file_path)

            is_scanned = doc_data.get("is_scanned", False)
            pages = doc_data.get("pages", [])

            scanned_pages = [p["page_number"] for p in pages if p.get("is_scanned")]

            return {
                "filename": os.path.basename(file_path),
                "is_valid_text": not is_scanned,
                "is_scanned": is_scanned,
                "scanned_pages": scanned_pages,
                "total_pages": len(pages),
                "message": (
                    "MANUAL REVIEW REQUIRED: File contains scanned/image-only pages. Automated analysis disabled for these pages."
                    if is_scanned else "Text-accessible document validated successfully."
                )
            }
        except Exception as e:
            logger.exception(f"Error validating file {file_path}: {e}")
            return {
                "filename": os.path.basename(file_path),
                "is_valid_text": False,
                "is_scanned": True,
                "scanned_pages": [],
                "total_pages": 0,
                "message": f"Error loading file: {str(e)}"
            }

    @staticmethod
    def check_extraction_confidence(extraction_data: Dict[str, Any], threshold: float = 0.7) -> List[str]:
        """Flags extraction fields with confidence below threshold."""
        warnings = []
        conf = extraction_data.get("extraction_confidence", 1.0)
        if conf < threshold:
            warnings.append(f"Low confidence ({conf:.2f}) on extracted fields. Manual verification required.")
        
        if not extraction_data.get("quoted_amount"):
            warnings.append("Quoted price missing or unparsed.")
            
        return warnings
