"""
Vendor Service for GeM TenderLens.
Manages vendor submission dossiers, email intake, and proposal data extraction.
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from schemas.vendor import VendorSubmission, VendorProposal
from rag.document_loader import DocumentLoader
from rag.chunking import DocumentChunker
from rag.chroma_client import ChromaDBClientManager
from rag.embeddings import VectorEmbeddingProvider
from utils_logger import get_logger

logger = get_logger(__name__)

from langsmith import traceable

VENDOR_STORAGE_DIR = "./data/uploads/vendor_submissions"


class VendorService:
    """Handles intake, parsing, extraction, and vector store indexing of vendor proposals."""

    def __init__(self, chroma_manager: Optional[ChromaDBClientManager] = None):
        self.storage_dir = VENDOR_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        self.chroma_manager = chroma_manager or ChromaDBClientManager()
        self.embedding_provider = VectorEmbeddingProvider()

    @traceable(name="Vendor Submission Intake")
    def process_vendor_submission(
        self,
        vendor_name: str,
        tender_id: str,
        file_paths: List[str],
        email_subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingests vendor proposal files, extracts structured fields, and indexes chunks into ChromaDB."""
        vendor_id = f"VEND_{re.sub(r'[^a-zA-Z0-9]', '', vendor_name).upper()[:10]}"
        logger.info(f"Processing vendor submission: '{vendor_name}' ({vendor_id}) for tender '{tender_id}'")

        try:
            submission = VendorSubmission(
                vendor_id=vendor_id,
                vendor_name=vendor_name,
                tender_id=tender_id,
                email_subject=email_subject or f"Proposal for {tender_id} from {vendor_name}",
                received_at=datetime.now(),
                revision_number=1,
                attachment_paths=file_paths
            )

            collection = self.chroma_manager.get_or_create_collection(tender_id)
            combined_text = []
            scanned_flags = []
            loaded_docs = []

            for fp in file_paths:
                doc_data = DocumentLoader.load_document(fp)
                loaded_docs.append((fp, doc_data))
                if doc_data.get("is_scanned"):
                    scanned_flags.append(os.path.basename(fp))
                for page in doc_data.get("pages", []):
                    combined_text.append(page.get("content", ""))

            full_proposal_text = "\n".join(combined_text)

            v_clean = re.sub(r'[^a-zA-Z0-9]', '_', vendor_name)
            for fp, doc_data in loaded_docs:
                fp_clean = re.sub(r'[^a-zA-Z0-9]', '_', os.path.basename(fp))
                v_doc_id = f"DOC_{tender_id.replace('/', '_')}_{v_clean}_{fp_clean}"
                chunks = DocumentChunker.chunk_document(
                    doc_data=doc_data,
                    tender_id=tender_id,
                    document_id=v_doc_id,
                    document_type="vendor_proposal"
                )
                if chunks:
                    texts = [f"Vendor: {vendor_name}\n" + c.text for c in chunks]
                    ids = [f"{vendor_id}_{fp_clean}_{c.chunk_id}" for c in chunks]
                    metadatas = [
                        {
                            "tender_id": c.tender_id,
                            "vendor_id": vendor_id,
                            "vendor_name": vendor_name,
                            "document_id": c.document_id,
                            "document_type": "vendor_proposal",
                            "document_version": "1.0",
                            "clause_id": f"Proposal: {vendor_name}",
                            "page_number": c.page_number or 1,
                            "mandatory_flag": c.mandatory_flag,
                            "source_file": f"{vendor_name} ({os.path.basename(fp)})"
                        }
                        for c in chunks
                    ]
                    embeddings = self.embedding_provider.embed_texts(texts)
                    collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
                    logger.info(f"Indexed {len(chunks)} vendor proposal chunks into ChromaDB for '{vendor_name}' ({os.path.basename(fp)})")

            proposal = self._extract_proposal_fields(vendor_id, full_proposal_text)

            return {
                "success": True,
                "submission": submission,
                "proposal": proposal,
                "full_text": full_proposal_text,
                "scanned_files": scanned_flags,
                "manual_review_required": len(scanned_flags) > 0
            }

        except Exception as e:
            logger.exception(f"Error processing vendor submission for '{vendor_name}': {e}")
            return {"success": False, "error": str(e)}

    def _extract_proposal_fields(self, vendor_id: str, text: str) -> VendorProposal:
        """Extracts numerical & technical values from text using regex and heuristics."""
        logger.info(f"Extracting proposal fields for vendor '{vendor_id}'")

        # Exclude lines mentioning past orders/experience
        clean_lines = [
            line for line in text.splitlines()
            if not any(past in line.lower() for past in ['past supply', 'prior supply', 'supply order', 'po no', 'past order', 'completion certificate'])
        ]
        clean_text = '\n'.join(clean_lines)
        text_lower = text.lower()

        # 1. Price extraction
        quoted_amount = None
        total_patterns = [
            r'(?:grand\s+total|total\s+amount|quoted\s+amount|final\s+bid)(?:[^\n\d]*)(?:rs\.?|inr|\u20b9)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:total|cost)[^\n\d]*(?:rs\.?|inr|\u20b9)?\s*([0-9,]{6,}(?:\.[0-9]{2})?)',
            r'(?:rs\.?|inr|\u20b9)\s*([0-9,]{6,}(?:\.[0-9]{2})?)'
        ]

        for pat in total_patterns:
            matches = re.findall(pat, clean_text, re.IGNORECASE)
            for m in matches:
                try:
                    val = float(m.replace(',', ''))
                    if val > 1000:
                        quoted_amount = val
                        break
                except ValueError:
                    pass
            if quoted_amount:
                break

        # 2. Tax & GST extraction
        is_before_gst = any(term in text_lower for term in ["before gst", "excl. gst", "excluding gst", "+18% gst", "+ 18% gst", "excl gst", "grand total before gst"])
        is_incl_gst = any(term in text_lower for term in ["incl. gst", "inclusive of gst", "incl gst", "total incl. gst", "total (incl. gst)"])

        tax_amount = 0.0
        if is_before_gst and quoted_amount:
            tax_amount = round(0.18 * quoted_amount, 2)
        elif not is_incl_gst and quoted_amount:
            tax_matches = re.findall(r'(?:gst|tax|vat)[:\s]*INR\s*([0-9,]+(?:\.[0-9]{2})?)|(?:gst|tax)[:\s]*([0-9]+)%', text, re.IGNORECASE)
            if tax_matches:
                flat_tax = [t for tup in tax_matches for t in tup if t]
                if flat_tax:
                    try:
                        tax_val = float(flat_tax[0].replace(",", ""))
                        tax_amount = round((tax_val / 100.0) * quoted_amount, 2) if tax_val < 100 else tax_val
                    except ValueError:
                        tax_amount = 0.0

        # 3. Delivery days
        delivery_days = 21
        deliv_patterns = [
            r'(?:delivery\s+(?:timeline|period|lead\s+time)?|deliver)[:\s]*(\d+)\s*(?:days|working days|calendar days)',
            r'(\d+)\s*days\s+(?:for\s+all\s+items|to|delivery)'
        ]
        for dpat in deliv_patterns:
            dmatches = re.findall(dpat, text, re.IGNORECASE)
            if dmatches:
                try:
                    delivery_days = int(dmatches[0])
                    break
                except ValueError:
                    pass

        # 4. Warranty months
        warranty_matches = re.findall(r'(\d+)\s*(?:months|month|years|year)\s*warranty', text, re.IGNORECASE)
        warranty_months = 12
        if warranty_matches:
            try:
                val = int(warranty_matches[0])
                warranty_months = val * 12 if "year" in text_lower else val
            except ValueError:
                warranty_months = 12

        # 5. Technical claims & certificates
        claims = []
        if any(term in text_lower for term in ["make", "publisher", "brand", "model"]):
            claims.append("Exact make/model and technical details provided.")
        if any(term in text_lower for term in ["spec", "compliant", "compliance"]):
            claims.append("Fully compliant with tender technical specifications.")
        if "delivery" in text_lower or "consignee" in text_lower:
            claims.append(f"Offered delivery schedule of {delivery_days} days.")

        certs = []
        cert_map = [
            (["udyam", "mse"], "MSE / Udyam Registration Certificate"),
            (["gst", "tax"], "GST Registration Certificate"),
            (["oem", "authorization"], "OEM Authorization Certificate"),
            (["iso", "9001"], "ISO 9001 Quality Certificate"),
            (["non-blacklisting", "blacklisting"], "Self-Declaration of Non-Blacklisting")
        ]
        for terms, cert_name in cert_map:
            if any(term in text_lower for term in terms):
                certs.append(cert_name)

        return VendorProposal(
            vendor_id=vendor_id,
            quoted_amount=quoted_amount,
            currency="INR",
            tax_amount=tax_amount,
            delivery_days=delivery_days,
            warranty_months=warranty_months,
            technical_claims=claims,
            certificates_submitted=certs,
            extraction_confidence=0.95 if quoted_amount else 0.60
        )
