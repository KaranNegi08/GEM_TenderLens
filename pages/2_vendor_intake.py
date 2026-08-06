"""
Vendor Intake Screen - GeM TenderLens.
Handles vendor submission ingestion, proposal email parsing, file dossier creation, and text accessibility validation.
"""

import streamlit as st
import os
from services.vendor_service import VendorService
from utils_logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Vendor Intake - GeM TenderLens", page_icon="📥", layout="wide")

st.title("📥 Vendor Submission Intake & Dossier Management")
st.caption("Upload vendor proposal emails and documents. Establish submission dossiers and flag scanned files.")

from services.tender_service import TenderService

vendor_service = VendorService()
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

col_a, col_b = st.columns([1, 2])

with col_a:
    st.subheader("1. Upload Vendor Submission")
    v_name_input = st.text_input("Vendor Company Name:", placeholder="e.g. Acme Supplies Ltd")
    v_files_uploaded = st.file_uploader(
        "Upload Proposal/PDF/EML Files:",
        type=["pdf", "docx", "eml", "txt", "xlsx"],
        accept_multiple_files=True
    )
    
    if st.button("Submit & Create Dossier", type="primary", use_container_width=True):
        if not v_name_input or not v_files_uploaded:
            st.warning("Please enter vendor company name and upload proposal files.")
        else:
            logger.info(f"Processing submission for vendor '{v_name_input}'")
            with st.spinner("Processing vendor submission..."):
                try:
                    saved_paths = []
                    v_dir = os.path.join("./data/uploads/vendor_submissions", v_name_input.replace(" ", "_"))
                    os.makedirs(v_dir, exist_ok=True)
                    for uf in v_files_uploaded:
                        sp = os.path.join(v_dir, uf.name)
                        with open(sp, "wb") as f:
                            f.write(uf.getbuffer())
                        saved_paths.append(sp)
                    
                    res = vendor_service.process_vendor_submission(v_name_input, st.session_state.active_tender_id, saved_paths)
                    if res.get("success"):
                        st.session_state.vendor_dossiers.append(res)
                        st.success(f"Dossier created for `{v_name_input}`!")
                except Exception as e:
                    logger.exception(f"Error creating vendor dossier: {e}")
                    st.error(f"Failed to upload submission: {str(e)}")

with col_b:
    st.subheader("2. Ingested Vendor Dossiers")
    if st.session_state.vendor_dossiers:
        for idx, dossier in enumerate(st.session_state.vendor_dossiers, 1):
            sub = dossier.get("submission")
            prop = dossier.get("proposal")
            v_name = sub.vendor_name if hasattr(sub, "vendor_name") else dossier.get("vendor_name", f"Vendor {idx}")
            q_amt = prop.quoted_amount if hasattr(prop, "quoted_amount") else 0.0
            
            with st.expander(f"📁 Vendor #{idx}: {v_name}", expanded=True):
                st.write(f"**Quoted Base Price:** INR {q_amt:,.2f}" if q_amt else "**Quoted Price:** Unparsed")
                st.write(f"**Offered Delivery:** {prop.delivery_days if hasattr(prop, 'delivery_days') else 21} Days")
                if dossier.get("manual_review_required"):
                    st.warning("⚠️ Document contains scanned/image-only pages. Manual review required.")
                else:
                    st.success("🟢 Text-accessible document verified.")
    else:
        st.info("No vendor submissions loaded yet. Upload vendor proposal files using the form on the left.")
