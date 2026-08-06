"""
Review & Export Screen - GeM TenderLens.
Provides human reviewer approval workflows, comment logs, and committee-ready report exports.
"""

import streamlit as st
import os
from services.export_service import ExportService
from utils_logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Review & Export - GeM TenderLens", page_icon="📝", layout="wide")

st.title("📝 Reviewer Sign-Off & Committee Report Export")
st.caption("Review AI findings, record procurement committee decisions, and export committee-ready comparison packages.")

from services.tender_service import TenderService

export_service = ExportService()
tender_service = TenderService()
available_tenders = tender_service.list_available_tenders()

# Standardized session state initialization
if "active_tender_id" not in st.session_state:
    st.session_state.active_tender_id = available_tenders[0] if available_tenders else "GEM_9146015"
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []
if "vendor_dossiers" not in st.session_state:
    st.session_state.vendor_dossiers = []
if "comparison_result" not in st.session_state:
    st.session_state.comparison_result = None
if "export_files" not in st.session_state:
    st.session_state.export_files = None
if "tender_indexed" not in st.session_state:
    st.session_state.tender_indexed = False

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

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Procurement Committee Sign-Off")
    status_opt = st.selectbox("Sign-Off Approval Status:", ["APPROVED_RECOMMENDED_FOR_AWARD", "PENDING_REVIEW", "CLARIFICATIONS_REQUESTED"])
    notes = st.text_area("Reviewer Comments / Observations:", placeholder="Record committee sign-off rationale...")

    if st.button("📄 Generate Committee Evaluation Package", type="primary"):
        if not st.session_state.get("comparison_result"):
            st.warning("Please run comparison in Page 4 first.")
        else:
            try:
                exp_res = export_service.generate_committee_report(
                    tender_id=st.session_state.active_tender_id,
                    comparison_matrix=st.session_state.comparison_result,
                    reviewer_notes=notes,
                    sign_off_status=status_opt
                )
                st.session_state.export_files = exp_res
                st.success("Report package generated!")
            except Exception as e:
                logger.exception(f"Error exporting report: {e}")
                st.error(f"Export failed: {str(e)}")

with col2:
    if st.session_state.get("export_files"):
        files = st.session_state.export_files
        st.subheader("2. Download Reports")
        if os.path.exists(files["markdown"]):
            with open(files["markdown"], "r", encoding="utf-8") as f:
                st.download_button("Download Markdown Report (.md)", data=f.read(), file_name=os.path.basename(files["markdown"]), mime="text/markdown")
        if os.path.exists(files["html"]):
            with open(files["html"], "r", encoding="utf-8") as f:
                st.download_button("Download HTML Package (.html)", data=f.read(), file_name=os.path.basename(files["html"]), mime="text/html")
        if os.path.exists(files["json"]):
            with open(files["json"], "r", encoding="utf-8") as f:
                st.download_button("Download Raw JSON Data (.json)", data=f.read(), file_name=os.path.basename(files["json"]), mime="application/json")

st.divider()

if st.session_state.get("export_files") and os.path.exists(st.session_state.export_files["markdown"]):
    st.subheader("3. Report Preview")
    with open(st.session_state.export_files["markdown"], "r", encoding="utf-8") as f:
        st.markdown(f.read())
