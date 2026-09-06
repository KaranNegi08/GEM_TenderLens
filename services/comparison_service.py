"""
Comparison Service for GeM TenderLens.
Generates technical compliance matrix, commercial cost normalization table, risk queue, and L-1 determination.
"""

from typing import List, Dict, Any, Tuple
from schemas.evaluation import EvaluationFinding, EvidenceCitation
from rag.retriever import KnowledgeRetriever
from utils_logger import get_logger
from utils.gst_helper import normalize_gst

logger = get_logger(__name__)


class ComparisonService:
    """Computes evidence-backed vendor comparisons, pricing ranks, and risk flags."""

    def __init__(self):
        self.retriever = KnowledgeRetriever()

    def generate_comparison_matrix(
        self,
        tender_id: str,
        vendor_dossiers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Executes technical, commercial, and risk analysis across submitted vendor dossiers."""
        logger.info(f"Generating comparison matrix for tender '{tender_id}' across {len(vendor_dossiers)} vendors.")

        try:
            # 1. Commercial cost normalization & L-1 evaluation
            commercial_comparison = self._compare_commercials(vendor_dossiers)

            # 2. Technical compliance matrix creation
            compliance_findings = self._evaluate_technical_compliance(tender_id, vendor_dossiers)

            # 3. Risk and clarification queue
            risk_queue = self._build_risk_queue(vendor_dossiers, compliance_findings)

            # 4. Guardrail: Determine Financial L-1 vs Technically Qualified L-1
            financial_l1_name = commercial_comparison[0]["vendor_name"] if commercial_comparison else "N/A"
            financial_l1_cost = commercial_comparison[0]["total_cost"] if commercial_comparison else 0.0

            l1_findings = [f for f in compliance_findings if f["vendor_name"] == financial_l1_name]
            l1_deviations = [f for f in l1_findings if f["status"] in ["non_compliant", "review_required"]]

            qualified_l1 = "N/A"
            qualified_l1_cost = 0.0
            for comm in commercial_comparison:
                v_name = comm["vendor_name"]
                v_findings = [f for f in compliance_findings if f["vendor_name"] == v_name]
                if all(f["status"] == "compliant" for f in v_findings):
                    qualified_l1 = v_name
                    qualified_l1_cost = comm["total_cost"]
                    break

            return {
                "tender_id": tender_id,
                "total_vendors": len(vendor_dossiers),
                "commercial_comparison": commercial_comparison,
                "compliance_findings": compliance_findings,
                "risk_queue": risk_queue,
                "l1_vendor": financial_l1_name,
                "l1_cost": financial_l1_cost,
                "l1_deviations_count": len(l1_deviations),
                "l1_qualified_vendor": qualified_l1 if qualified_l1 != "N/A" else financial_l1_name,
                "l1_qualified_cost": qualified_l1_cost
            }
        except Exception as e:
            logger.exception(f"Error generating comparison matrix for tender '{tender_id}': {e}")
            raise

    @staticmethod
    def _get_prop_attr(prop: Any, attr: str, default: Any) -> Any:
        """Helper to get attribute or dict key with default fallback."""
        if hasattr(prop, attr):
            return getattr(prop, attr) or default
        if isinstance(prop, dict):
            return prop.get(attr, default)
        return default

    @staticmethod
    def _extract_dossier_info(dossier: Dict[str, Any]) -> Tuple[str, str, Any, str]:
        """Extracts vendor_id, vendor_name, proposal object/dict, and lowercase full_text cleanly."""
        sub = dossier.get("submission")
        v_name = getattr(sub, "vendor_name", None) or dossier.get("vendor_name", "Unknown Vendor")
        v_id = getattr(sub, "vendor_id", None) or dossier.get("vendor_id", "VEND_000")
        prop = dossier.get("proposal")
        full_text = dossier.get("full_text", "").lower()
        return v_id, v_name, prop, full_text

    def _compare_commercials(self, vendor_dossiers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalizes quoted base prices, taxes, total cost, warranty, and ranks vendors."""
        commercials = []
        for dossier in vendor_dossiers:
            v_id, v_name, prop, full_text = self._extract_dossier_info(dossier)

            base_price = self._get_prop_attr(prop, "quoted_amount", 0.0)
            tax = self._get_prop_attr(prop, "tax_amount", 0.0)
            delivery = self._get_prop_attr(prop, "delivery_days", 21)
            warranty = self._get_prop_attr(prop, "warranty_months", 12)
            certs = self._get_prop_attr(prop, "certificates_submitted", []) or []

            # Pre-tax detection and standard 18% GST normalization
            tax = normalize_gst(full_text, base_price, tax)

            total_cost = base_price + tax
            tax_note = f"₹{tax:,.2f} (18% GST Added)" if tax > 0 else "Included in Base Quote"

            commercials.append({
                "vendor_id": v_id,
                "vendor_name": v_name,
                "base_price": base_price,
                "tax_amount": tax,
                "tax_note": tax_note,
                "total_cost": total_cost,
                "delivery_days": delivery,
                "warranty_months": warranty,
                "mse_status": "Yes (Udyam Verified)" if any("Udyam" in c for c in certs) else "No",
                "rank": 1
            })

        commercials.sort(key=lambda x: x["total_cost"])
        for idx, item in enumerate(commercials):
            item["rank"] = idx + 1
            item["l_status"] = f"L-{idx + 1}"

        return commercials

    def _evaluate_technical_compliance(
        self,
        tender_id: str,
        vendor_dossiers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Maps mandatory tender requirements against vendor evidence dynamically."""
        from services.tender_service import TenderService
        from utils.evaluator_helper import evaluate_generic_requirement

        findings = []
        stored_requirements = TenderService.get_stored_requirements(tender_id)

        # Dynamic ChromaDB Retrieval Fallback: If no requirements are saved in DB for this tender_id,
        # query ChromaDB for indexed bid document requirement chunks dynamically.
        if not stored_requirements:
            try:
                bid_chunks = self.retriever.search_tender_knowledge(
                    tender_id=tender_id,
                    query="mandatory requirement technical specification boq clause eligibility warranty delivery",
                    n_results=8
                )
                dynamic_chunks = [
                    c for c in bid_chunks
                    if str(c.get("metadata", {}).get("document_type", "")).lower() in ["bid_document", "technical_spec", "boq"]
                    or "corrigendum" not in str(c.get("metadata", {}).get("document_type", "")).lower()
                ]
                for idx, chunk in enumerate(dynamic_chunks, start=1):
                    meta = chunk.get("metadata", {})
                    c_id = meta.get("clause_id") or f"CLAUSE_{idx}"
                    txt_snippet = chunk.get("text", "")[:120].strip()
                    stored_requirements.append({
                        "requirement_id": meta.get("requirement_id") or c_id or f"REQ_{idx}",
                        "name": txt_snippet if txt_snippet else f"Requirement {idx}",
                        "requirement_text": chunk.get("text", ""),
                        "clause_id": c_id,
                        "page_number": meta.get("page_number", 1)
                    })
            except Exception as search_err:
                logger.warning(f"Could not perform dynamic ChromaDB search for requirements of tender '{tender_id}': {search_err}")

        if not stored_requirements:
            logger.info(f"No stored or indexed requirements found for tender '{tender_id}'")
            return findings

        # 1. Live Multi-Hop Retrieval: Query ChromaDB for active tender corrigenda / amendments
        live_corrigenda_chunks = []
        try:
            corr_search = self.retriever.search_tender_knowledge(
                tender_id=tender_id,
                query="corrigendum addendum amendment specification warranty delivery requirement clause",
                n_results=5
            )
            live_corrigenda_chunks = [
                c for c in corr_search
                if str(c.get("metadata", {}).get("document_type", "")).lower() == "corrigendum"
                or "corrigendum" in str(c.get("metadata", {}).get("source_file", "")).lower()
                or "addendum" in str(c.get("metadata", {}).get("source_file", "")).lower()
            ]
        except Exception as corr_err:
            logger.warning(f"Could not perform live corrigenda search for tender '{tender_id}': {corr_err}")

        corrigendum_combined_text = " ".join([c["text"] for c in live_corrigenda_chunks])

        for dossier in vendor_dossiers:
            v_id, v_name, prop, full_text = self._extract_dossier_info(dossier)

            # 2. Live Multi-Hop Retrieval: Query ChromaDB for live multi-document vendor evidence
            live_vendor_text = ""
            try:
                v_search = self.retriever.search_tender_knowledge(
                    tender_id=tender_id,
                    query=f"vendor {v_name} proposal specification warranty delivery certificate",
                    n_results=4,
                    document_type="vendor_proposal"
                )
                live_vendor_text = " ".join([c["text"] for c in v_search])
            except Exception as v_err:
                logger.debug(f"Live vendor evidence query notice for vendor '{v_name}': {v_err}")

            combined_vendor_text = (full_text + " " + live_vendor_text).strip()

            for req in stored_requirements:
                r_id = req.get("requirement_id") or req.get("id") or "REQ_GENERIC"
                req_name = req.get("name") or req.get("requirement_name") or req.get("requirement_text", "")[:80]
                clause_id = req.get("clause_id") or r_id

                status, explanation, confidence = evaluate_generic_requirement(
                    req, combined_vendor_text, prop,
                    corrigendum_text=corrigendum_combined_text,
                    vendor_evidence_text=live_vendor_text
                )

                # Determine Tender Citation (referencing Corrigendum if live corrigendum chunk matches requirement)
                tender_source_file = f"GeM_Bid_{tender_id}.pdf"
                tender_page = req.get("page_number") or 1
                tender_clause = clause_id
                tender_excerpt = f"Mandatory Requirement: {req_name}"

                matching_corr = [
                    c for c in live_corrigenda_chunks
                    if any(k in c["text"].lower() for k in req_name.lower().split() if len(k) > 3)
                ]
                if matching_corr:
                    top_corr = matching_corr[0]
                    corr_meta = top_corr.get("metadata", {})
                    tender_source_file = corr_meta.get("source_file", tender_source_file)
                    tender_page = corr_meta.get("page_number", 1)
                    tender_clause = corr_meta.get("clause_id", "CORRIGENDUM_CLAUSE")
                    tender_excerpt = f"[Latest Corrigendum Override] {top_corr['text'][:200]}..."

                tender_cit = EvidenceCitation(
                    source_file=tender_source_file,
                    page_number=tender_page,
                    clause_id=tender_clause,
                    excerpt=tender_excerpt
                )

                vendor_cit = EvidenceCitation(
                    source_file=f"{v_name}_Proposal.pdf",
                    page_number=1,
                    clause_id="PROPOSAL_PAGE_1",
                    excerpt=explanation
                )

                finding = EvaluationFinding(
                    vendor_id=v_id,
                    requirement_id=r_id,
                    status=status,
                    explanation=explanation,
                    tender_evidence=tender_cit,
                    vendor_evidence=vendor_cit,
                    confidence=confidence,
                    reviewer_status="pending"
                )

                findings.append({
                    "vendor_id": v_id,
                    "vendor_name": v_name,
                    "requirement_id": r_id,
                    "requirement_name": req_name,
                    "status": status,
                    "explanation": explanation,
                    "confidence": confidence,
                    "finding_object": finding
                })

        return findings

    def _build_risk_queue(
        self,
        vendor_dossiers: List[Dict[str, Any]],
        compliance_findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identifies missing documentation, low-confidence extractions, and draft clarification items."""
        risk_queue = []

        for f in compliance_findings:
            if f["status"] in ["review_required", "non_compliant", "partial"]:
                risk_queue.append({
                    "vendor_name": f["vendor_name"],
                    "issue_type": f["status"].upper(),
                    "description": f"{f['requirement_name']}: {f['explanation']}",
                    "confidence": f["confidence"],
                    "suggested_action": f"Request clarification or supporting document from {f['vendor_name']}."
                })

        for dossier in vendor_dossiers:
            v_id, v_name, _, _ = self._extract_dossier_info(dossier)
            if dossier.get("manual_review_required"):
                risk_queue.append({
                    "vendor_name": v_name,
                    "issue_type": "SCANNED_DOCUMENT_WARNING",
                    "description": "Vendor document contains scanned/image-only pages. Manual review required.",
                    "confidence": 0.50,
                    "suggested_action": "Manually verify original scanned PDF document."
                })

        return risk_queue
