"""
Vendor Service for GeM TenderLens.
Manages vendor submission dossiers, email intake, and proposal data extraction.
"""

import os
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from schemas.vendor import VendorSubmission, VendorProposal
from rag.document_loader import DocumentLoader
from rag.chunking import DocumentChunker
from rag.chroma_client import ChromaDBClientManager
from rag.embeddings import VectorEmbeddingProvider
from services.validation_service import ValidationService
from utils_logger import get_logger
from utils.gst_helper import normalize_gst

logger = get_logger(__name__)

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

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
        name_clean = re.sub(r'[^a-zA-Z0-9]', '', vendor_name).upper()[:10]
        name_hash = hashlib.md5(vendor_name.encode()).hexdigest()[:4].upper()
        vendor_id = f"VEND_{name_clean}_{name_hash}"
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
                val_res = ValidationService.validate_file_accessibility(fp, doc_data=doc_data)
                if val_res.get("is_scanned"):
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

            # Audit Log: Record vendor intake event
            try:
                from services.audit_service import DatabaseAuditService
                from schemas.audit import AuditLog
                import uuid

                audit_log = AuditLog(
                    log_id=f"AUDIT_{uuid.uuid4().hex[:12].upper()}",
                    actor="VendorService",
                    action_type="VENDOR_INTAKE",
                    details={
                        "vendor_name": vendor_name,
                        "vendor_id": vendor_id,
                        "tender_id": tender_id,
                        "scanned_files_count": len(scanned_flags)
                    }
                )
                DatabaseAuditService.save_audit_log(audit_log)
            except Exception as audit_err:
                logger.warning(f"Could not save audit log for vendor submission '{vendor_name}': {audit_err}")

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
        """Extracts numerical & technical values from text using consolidated proposal_extractor utility."""
        from utils.proposal_extractor import extract_proposal_fields_from_text
        return extract_proposal_fields_from_text(vendor_id, text)
