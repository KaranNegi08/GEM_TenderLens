"""
RAG Search Screen - GeM TenderLens.
Executes natural language queries against ChromaDB knowledge base with metadata-filtered clause citations.
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from rag.retriever import KnowledgeRetriever
from rag.document_loader import DocumentLoader
from utils_logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Tender RAG Search - GeM TenderLens", page_icon="🔍", layout="wide")

st.title("🔍 Tender Knowledge Base RAG Search")
st.caption("Search governing tender clauses and technical specifications with file and page citations.")

from services.tender_service import TenderService

retriever = KnowledgeRetriever()
tender_service = TenderService()
available_tenders = tender_service.list_available_tenders()

# Standardized session state initialization
from utils.session_state import init_session_state
init_session_state(available_tenders)

# Sidebar Navigation
with st.sidebar:
    st.title("GeM TenderLens")
    st.caption("Active Tender: " + st.session_state.active_tender_id)
    st.divider()
    st.page_link("app.py", label="Home Page", icon="🏠")
    st.page_link("pages/1_tender_workspace.py", label="1. Tender Workspace", icon="📂")
    st.page_link("pages/2_vendor_intake.py", label="2. Vendor Intake", icon="📥")
    st.page_link("pages/3_rag_search.py", label="3. Tender RAG Search", icon="🔍")
    st.page_link("pages/4_vendor_comparison.py", label="4. Vendor Comparison", icon="📊")
    st.page_link("pages/5_review_export.py", label="5. Review & Export", icon="📝")



query_text = st.text_input(
    "Enter query or clause question:",
    value="",
    placeholder="e.g. What are the delivery terms or EMD requirements?"
)

if st.button("🔎 Execute RAG Search", type="primary"):
    if not query_text.strip():
        st.warning("Please enter a search query.")
    else:
        logger.info(f"Executing RAG search query '{query_text}' for tender '{st.session_state.active_tender_id}'")
        with st.spinner("Searching ChromaDB collection & synthesizing answer..."):
            try:
                synthesis_response = retriever.synthesize_answer(
                    tender_id=st.session_state.active_tender_id,
                    query=query_text,
                    n_results=3
                )
                results = synthesis_response.get("results", [])
                synthesized_ans = synthesis_response.get("synthesized_answer", "")

                # Audit Log persistence for RAG Search
                try:
                    from services.audit_service import DatabaseAuditService
                    from schemas.audit import AuditLog
                    import uuid

                    audit_log = AuditLog(
                        log_id=f"AUDIT_{uuid.uuid4().hex[:12].upper()}",
                        actor="User",
                        action_type="RAG_SEARCH",
                        details={
                            "tender_id": st.session_state.active_tender_id,
                            "query": query_text,
                            "results_count": len(results),
                            "has_synthesized_answer": bool(synthesized_ans)
                        }
                    )
                    DatabaseAuditService.save_audit_log(audit_log)
                except Exception as audit_err:
                    logger.warning(f"Could not save RAG search audit log: {audit_err}")

                if synthesized_ans:
                    st.markdown("### 💡 Synthesized Direct Answer")
                    if synthesized_ans.startswith("⚠️"):
                        st.warning(synthesized_ans)
                    else:
                        st.success(f"**Answer:** {synthesized_ans}")
                    st.divider()

                if results:
                    st.markdown(f"### 📄 Source Clause Citations ({len(results)})")
                    for idx, res in enumerate(results, 1):
                        meta = res.get("metadata", {})
                        # DocumentLoader centrally cleans text for all formats during ingestion.
                        # Kept here as an extra safety-net for UI rendering.
                        clean_text = DocumentLoader.clean_english_text(res.get("text", ""))
                        snippet_text = DocumentLoader.clean_english_text(res.get("snippet", ""))
                        clause_tag = meta.get("clause_id") or f"Page {meta.get('page_number')}"
                        relevance_pct = round(max(0.0, min(100.0, (1.0 - res.get("distance", 0.0)) * 100.0)), 1)

                        with st.container(border=True):
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.markdown(f"#### Citation #{idx}: `{clause_tag}`")
                                st.write(f"📄 **Source File:** `{meta.get('source_file')}` | **Page:** `{meta.get('page_number')}` | **Clause ID:** `{clause_tag}`")
                            with col_b:
                                st.metric(label="Relevance", value=f"{relevance_pct}%")

                            st.info(f"**Key Matching Excerpt:**\n{snippet_text if snippet_text else clean_text[:250]}")
                            with st.expander("📖 Show Full Clause Chunk Text"):
                                st.write(clean_text)
                elif not synthesized_ans.startswith("⚠️"):
                    st.warning("No matching clauses found in ChromaDB. Ensure documents are loaded in Page 1 (Tender Workspace).")
            except Exception as e:
                logger.exception(f"Error executing RAG search: {e}")
                st.error(f"Search failed: {str(e)}")

