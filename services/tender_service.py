"""
Tender Service for GeM TenderLens.
Manages tender workspace lifecycles, requirement extractions, document processing, and ChromaDB indexing.
"""

import os
from typing import List, Dict, Any, Optional
from schemas.tender import TenderDocument, TenderRequirement
from rag.document_loader import DocumentLoader
from rag.chunking import DocumentChunker
from rag.chroma_client import ChromaDBClientManager
from rag.embeddings import VectorEmbeddingProvider
from services.validation_service import ValidationService
from utils_logger import get_logger

logger = get_logger(__name__)

TENDER_STORAGE_DIR = "./data/uploads/tender_documents"


class TenderService:
    """Service Layer for Tender Package Management."""

    def __init__(self, chroma_manager: Optional[ChromaDBClientManager] = None):
        self.storage_dir = TENDER_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        self.chroma_manager = chroma_manager or ChromaDBClientManager()
        self.embedding_provider = VectorEmbeddingProvider()

    def list_available_tenders(self) -> List[str]:
        """Scans the tender storage directory for available tender package folders and returns tender IDs."""
        if not os.path.exists(self.storage_dir):
            return []
        return sorted([
            item for item in os.listdir(self.storage_dir)
            if os.path.isdir(os.path.join(self.storage_dir, item))
        ])

    def get_tender_files(self, tender_id: str) -> List[str]:
        """Returns full paths of all document files belonging to the specified tender_id folder."""
        clean_id = tender_id.replace("/", "_")
        folder_path = os.path.join(self.storage_dir, clean_id)
        file_list = []

        if os.path.isdir(folder_path):
            file_list = [
                os.path.join(folder_path, fname)
                for fname in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, fname))
            ]
        elif os.path.exists(self.storage_dir):
            file_list = [
                os.path.join(self.storage_dir, fname)
                for fname in os.listdir(self.storage_dir)
                if os.path.isfile(os.path.join(self.storage_dir, fname)) and clean_id.lower() in fname.lower()
            ]

        return sorted(file_list)

    @staticmethod
    def infer_document_type(filename: str) -> str:
        """Infers document category based on filename keywords."""
        fn_lower = filename.lower()
        if "boq" in fn_lower:
            return "boq"
        if "tech" in fn_lower or "spec" in fn_lower:
            return "technical_spec"
        if any(term in fn_lower for term in ["atc", "terms", "payment"]):
            return "corrigendum"
        return "bid_document"

    def process_tender_package(self, tender_id: str) -> Dict[str, Any]:
        """Processes and indexes all document files inside a tender package folder."""
        """It is basically a Orchestrator"""
        file_paths = self.get_tender_files(tender_id)
        logger.info(f"Processing tender package for '{tender_id}' with {len(file_paths)} files.")

        self.chroma_manager.reset_collection(tender_id)

        results = []
        total_chunks = 0
        indexed_files = []

        for fp in file_paths:
            doc_type = self.infer_document_type(os.path.basename(fp))
            res = self.process_tender_file(fp, tender_id, document_type=doc_type)
            results.append(res)
            if res.get("success"):
                total_chunks += res.get("chunks_indexed", 0)
                indexed_files.append(fp)

        # Re-index existing vendor submissions for this tender if present
        try:
            from services.vendor_service import VendorService, VENDOR_STORAGE_DIR
            vs = VendorService(chroma_manager=self.chroma_manager)
            if os.path.exists(VENDOR_STORAGE_DIR):
                for v_folder in os.listdir(VENDOR_STORAGE_DIR):
                    v_dir = os.path.join(VENDOR_STORAGE_DIR, v_folder)
                    if os.path.isdir(v_dir):
                        v_files = [os.path.join(v_dir, f) for f in os.listdir(v_dir) if os.path.isfile(os.path.join(v_dir, f))]
                        if v_files:
                            v_name = v_folder.replace("_", " ")
                            v_res = vs.process_vendor_submission(v_name, tender_id, v_files)
                            if v_res.get("success"):
                                logger.info(f"Automatically re-indexed vendor '{v_name}' for tender '{tender_id}'")
        except Exception as v_err:
            logger.warning(f"Could not auto-re-index vendor submissions for tender '{tender_id}': {v_err}")

        # Audit Log: Record tender package processing event
        try:
            from services.audit_service import DatabaseAuditService
            from schemas.audit import AuditLog
            import uuid

            audit_log = AuditLog(
                log_id=f"AUDIT_{uuid.uuid4().hex[:12].upper()}",
                actor="TenderService",
                action_type="TENDER_UPLOAD",
                details={
                    "tender_id": tender_id,
                    "total_files": len(file_paths),
                    "indexed_files": len(indexed_files),
                    "total_chunks": total_chunks
                }
            )
            DatabaseAuditService.save_audit_log(audit_log)
        except Exception as audit_err:
            logger.warning(f"Could not save audit log for tender package '{tender_id}': {audit_err}")

        return {
            "success": len(indexed_files) > 0,
            "tender_id": tender_id,
            "total_files": len(file_paths),
            "indexed_files": indexed_files,
            "total_chunks": total_chunks,
            "details": results
        }

    def process_tender_file(
        self,
        file_path: str,
        tender_id: str,
        document_type: str = "bid_document",
        document_version: str = "1.0"
    ) -> Dict[str, Any]:
        """Parses uploaded tender document, extracts requirements, chunks content, and indexes into ChromaDB."""
        filename = os.path.basename(file_path)
        logger.info(f"Processing tender file '{filename}' for tender_id '{tender_id}'")

        try:
            doc_data = DocumentLoader.load_document(file_path)
            if doc_data.get("error"):
                logger.error(f"Failed to load document {filename}: {doc_data['error']}")
                return {"success": False, "error": doc_data["error"]}

            val_res = ValidationService.validate_file_accessibility(file_path, doc_data=doc_data)

            clean_tender_id = tender_id.replace("/", "_")
            doc_id = f"DOC_{clean_tender_id}_{document_type}_{document_version}"

            tender_doc = TenderDocument(
                tender_id=tender_id,
                document_id=doc_id,
                document_type=document_type,
                document_version=document_version,
                source_file=filename,
                is_governing_document=True
            )

            chunks = DocumentChunker.chunk_document(
                doc_data=doc_data,
                tender_id=tender_id,
                document_id=doc_id,
                document_type=document_type,
                document_version=document_version
            )

            collection = self.chroma_manager.get_or_create_collection(tender_id)

            if chunks:
                texts = [c.text for c in chunks]
                ids = [c.chunk_id for c in chunks]
                metadatas = [
                    {
                        "tender_id": c.tender_id,
                        "document_id": c.document_id,
                        "document_type": c.document_type,
                        "document_version": c.document_version,
                        "clause_id": c.clause_id or "",
                        "page_number": c.page_number or 1,
                        "mandatory_flag": c.mandatory_flag,
                        "effective_date": c.effective_date or "",
                        "source_file": c.source_file
                    }
                    for c in chunks
                ]
                embeddings = self.embedding_provider.embed_texts(texts)
                collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
                logger.info(f"Successfully indexed {len(chunks)} chunks into ChromaDB for tender '{tender_id}'")

            requirements = self._extract_requirements_from_chunks(chunks, tender_id)
            if requirements:
                self.save_requirements_to_db(tender_id, requirements)

            # Audit Log persistence
            try:
                from services.audit_service import DatabaseAuditService
                from schemas.audit import AuditLog
                import uuid

                audit_log = AuditLog(
                    log_id=f"AUDIT_{uuid.uuid4().hex[:12].upper()}",
                    actor="TenderService",
                    action_type="TENDER_UPLOAD",
                    details={
                        "tender_id": tender_id,
                        "source_file": filename,
                        "document_type": document_type,
                        "chunks_indexed": len(chunks),
                        "requirements_found": len(requirements)
                    }
                )
                DatabaseAuditService.save_audit_log(audit_log)
            except Exception as audit_err:
                logger.warning(f"Could not save audit log for tender file '{filename}': {audit_err}")

            return {
                "success": True,
                "tender_document": tender_doc,
                "chunks_indexed": len(chunks),
                "requirements_found": len(requirements),
                "requirements": requirements,
                "is_scanned": val_res.get("is_scanned", False),
                "scanned_pages": val_res.get("scanned_pages", [])
            }

        except Exception as e:
            logger.exception(f"Error processing tender file '{filename}': {e}")
            return {"success": False, "error": str(e)}

    def _extract_requirements_from_chunks(self, chunks: List[Any], tender_id: str) -> List[TenderRequirement]:
        """Scans chunks for mandatory technical or commercial requirements."""
        requirements: List[TenderRequirement] = []
        req_counter = 1

        for c in chunks:
            if c.mandatory_flag or any(k in c.text.lower() for k in ["technical specification", "boq title", "turnover", "experience"]):
                req = TenderRequirement(
                    requirement_id=f"REQ_{tender_id}_{req_counter:03d}",
                    tender_id=tender_id,
                    clause_id=c.clause_id,
                    requirement_text=c.text[:300],
                    requirement_type="technical" if "spec" in c.text.lower() or "boq" in c.text.lower() else "eligibility",
                    is_mandatory=c.mandatory_flag,
                    evidence_required="Certificate / Quotation / Specification Sheet",
                    page_number=c.page_number
                )
                requirements.append(req)
                req_counter += 1

        return requirements

    @staticmethod
    def save_requirements_to_db(tender_id: str, requirements: List[TenderRequirement]) -> bool:
        """Persists extracted TenderRequirement objects into DB."""
        try:
            from services.database import get_db_session, init_db
            from services.db_models import TenderRequirementORM
            init_db()

            with get_db_session() as session:
                session.query(TenderRequirementORM).filter(TenderRequirementORM.tender_id == tender_id).delete()
                orm_records = [
                    TenderRequirementORM(
                        requirement_id=r.requirement_id,
                        tender_id=r.tender_id,
                        clause_id=r.clause_id,
                        requirement_text=r.requirement_text,
                        requirement_type=r.requirement_type,
                        is_mandatory=r.is_mandatory,
                        evidence_required=r.evidence_required,
                        page_number=r.page_number
                    )
                    for r in requirements
                ]
                session.add_all(orm_records)
                logger.info(f"Persisted {len(orm_records)} TenderRequirements into DB for tender '{tender_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to persist requirements to DB for tender '{tender_id}': {e}")
            return False

    @staticmethod
    def get_stored_requirements(tender_id: str) -> List[Dict[str, Any]]:
        """Fetches stored TenderRequirement records from DB for a given tender_id."""
        try:
            from services.database import get_db_session
            from services.db_models import TenderRequirementORM

            with get_db_session() as session:
                records = session.query(TenderRequirementORM).filter(TenderRequirementORM.tender_id == tender_id).all()
                return [
                    {
                        "requirement_id": r.requirement_id,
                        "tender_id": r.tender_id,
                        "clause_id": r.clause_id or "GEN_CLAUSE",
                        "requirement_text": r.requirement_text,
                        "requirement_type": r.requirement_type,
                        "is_mandatory": r.is_mandatory,
                        "evidence_required": r.evidence_required,
                        "page_number": r.page_number or 1
                    }
                    for r in records
                ]
        except Exception as e:
            logger.error(f"Error fetching stored requirements from DB for '{tender_id}': {e}")
            return []

