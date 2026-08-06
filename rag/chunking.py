"""
Chunking Module for GeM TenderLens.
Chunks tender content by clause, section, or BOQ line item with complete metadata tags.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from utils_logger import get_logger

logger = get_logger(__name__)

class TextChunk(BaseModel):
    """Represents a chunk of text with exact document citation metadata."""
    chunk_id: str = Field(..., description="Unique chunk key")
    text: str = Field(..., description="Chunk content text")
    tender_id: str
    document_id: str
    document_type: str
    document_version: str = "1.0"
    clause_id: Optional[str] = None
    page_number: Optional[int] = 1
    mandatory_flag: bool = False
    effective_date: Optional[str] = None
    source_file: str

MANDATORY_KEYWORDS = (
    "mandatory", "shall be required", "must comply", "eligibility criteria",
    "experience criteria", "turnover criteria", "technical specification",
    "emd", "delivery period", "warranty", "penalty"
)


class DocumentChunker:
    """
    Chunks document pages into metadata-enriched text chunks for vector indexing.

    Chunking Strategy (3 Steps):
        1. Heading Recognition: Detect clause & section headers (e.g. BOQ, EMD, ATC).
        2. Paragraph Grouping: Group sentences up to ~1200 characters with 150-char overlap.
        3. Metadata Tagging: Attach page_number, clause_id, document_type & source_file.
    """

    @staticmethod
    def _extract_clause_heading(line: str) -> Optional[str]:
        """Extracts major clause header or section title from text line if present."""
        line_clean = line.strip()
        if not line_clean:
            return None

        # Ignore literal table header text like "Clause ID", "Clause No", "Clause Number", "Requirement Name"
        if re.match(r'^(?:clause\s*(?:id|no|number|#|title|name|description)|requirement\s*(?:id|no|number|name))', line_clean, re.IGNORECASE):
            return None

        # Ignore sub-item codes / bullet prefixes (like ELG-01, TS-05, WAR-02, Adjustability:, etc.)
        # so sub-rows and table elements stay TOGETHER inside the parent clause chunk
        if re.match(r'^(?:[A-Z]{2,4}-\d{1,3}|adjustability|back support|base|warranty|color|material|dimensions|weight|capacity|model|brand|make|origin|feature|note)[:\s-]', line_clean, re.IGNORECASE):
            return None


        # Patterns matching explicit MAJOR clause/section/metadata headings
        patterns = [
            r'^(?:clause|section|item|rule|sub-clause|part)\s*([0-9A-Za-z\.\s_-]{1,40})',
            r'^(\d+\.[\d\.]*\s+[A-Za-z0-9\s_-]{3,50})',
            r'^(emd\s*(?:amount|detail|exemption|pbg)?|epbg\s*(?:detail|percentage)?|delivery\s*(?:period|days)|warranty\s*(?:period|months)|turnover\s*criteria|experience\s*criteria|eligibility\s*criteria)',
            r'^(bid\s*details|technical\s*specifications?|generic|scope\s*of\s*supply|consignees?\s*reporting\s*officer)',
            r'^(commercial\s*(?:quotation|offer|terms)?|payment\s*(?:terms|conditions|schedule)|delivery\s*&\s*warranty|compliance\s*details)',
        ]

        for pat in patterns:
            m = re.search(pat, line_clean, re.IGNORECASE)
            if m:
                heading = m.group(0).strip(" :\t\r\n")
                if 3 <= len(heading) <= 60:
                    return heading
        return None


    @staticmethod
    def chunk_document(
        doc_data: Dict[str, Any],
        tender_id: str,
        document_id: str,
        document_type: str = "bid_document",
        document_version: str = "1.0",
        effective_date: Optional[str] = None,
        max_chunk_chars: int = 1200,
        overlap_chars: int = 150
    ) -> List[TextChunk]:

        """
        Chunks parsed document pages into fine-grained clause-level chunks.
        
        Args:
            doc_data (Dict): Output from DocumentLoader.load_document
            tender_id (str): Associated tender workspace ID
            document_id (str): Unique doc ID
            document_type (str): bid_document, boq, technical_spec, corrigendum
            document_version (str): Version string
            effective_date (str): Effective date string
            max_chunk_chars (int): Target maximum characters per chunk (~50-80 words)
            overlap_chars (int): Overlap character count
        """
        chunks: List[TextChunk] = []
        source_file = doc_data.get("filename", "unknown.pdf")
        pages = doc_data.get("pages", [])

        logger.info(f"Chunking document '{source_file}' ({len(pages)} pages) for tender '{tender_id}'")

        try:
            chunk_counter = 1
            active_clause_id: Optional[str] = None

            def _create_and_append_chunk(buf_text: str, p_num: int) -> TextChunk:
                nonlocal chunk_counter
                effective_clause = active_clause_id or f"Page {p_num} Clause"
                buf_mandatory = any(kw in buf_text.lower() for kw in MANDATORY_KEYWORDS)
                c_id = f"{document_id}_p{p_num}_c{chunk_counter}"
                chunk_counter += 1
                return TextChunk(
                    chunk_id=c_id,
                    text=buf_text.strip(),
                    tender_id=tender_id,
                    document_id=document_id,
                    document_type=document_type,
                    document_version=document_version,
                    clause_id=effective_clause,
                    page_number=p_num,
                    mandatory_flag=buf_mandatory,
                    effective_date=effective_date,
                    source_file=source_file
                )

            for page in pages:
                page_num = page.get("page_number", 1)
                page_text = page.get("content", "")
                if not page_text.strip():
                    continue

                lines = [l.strip() for l in page_text.splitlines() if l.strip()]
                current_text_buf = ""

                for line in lines:
                    new_heading = DocumentChunker._extract_clause_heading(line)

                    # Flush immediately when a new clause heading appears
                    if new_heading and current_text_buf.strip():
                        chunks.append(_create_and_append_chunk(current_text_buf, page_num))
                        current_text_buf = ""

                    if new_heading:
                        active_clause_id = new_heading

                    # If adding line exceeds max_chunk_chars, flush buffer
                    if current_text_buf and (len(current_text_buf) + len(line) > max_chunk_chars):
                        chunks.append(_create_and_append_chunk(current_text_buf, page_num))
                        overlap_point = max(0, len(current_text_buf) - overlap_chars)
                        current_text_buf = current_text_buf[overlap_point:].strip() + "\n" + line
                    else:
                        current_text_buf = (current_text_buf + "\n" + line).strip()

                # Flush remaining text for page
                if current_text_buf.strip():
                    chunks.append(_create_and_append_chunk(current_text_buf, page_num))

            logger.info(f"Generated {len(chunks)} fine-grained clause chunks for document '{source_file}'")
            return chunks

        except Exception as e:
            logger.exception(f"Error chunking document {source_file}: {e}")
            raise


