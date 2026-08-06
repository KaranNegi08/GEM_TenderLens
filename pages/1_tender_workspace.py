"""
Tender Workspace Screen - GeM TenderLens.
Handles tender document upload, selection, version register, and ChromaDB vector store indexing.
"""

import streamlit as st
import os
from services.tender_service import TenderService
from utils_logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Tender Workspace - GeM TenderLens", page_icon="📂", layout="wide")

st.title("📂 Tender Workspace & Package Management")
st.caption("Upload governing GeM tender documents and build isolated ChromaDB vector indices.")

tender_service = TenderService()

# Available tender package folders in data/uploads/tender_documents/
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

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("1. Active Tender Setup")
    
    if available_tenders:
        selected_tender_folder = st.selectbox(
            "Select Available Tender Package Folder:",
            options=available_tenders + ["➕ Enter Custom Tender ID"],
            index=available_tenders.index(st.session_state.active_tender_id) if st.session_state.active_tender_id in available_tenders else 0
        )
        if selected_tender_folder == "➕ Enter Custom Tender ID":
            tender_id_input = st.text_input("Custom GeM Tender Reference ID:", value=st.session_state.active_tender_id)
        else:
            tender_id_input = selected_tender_folder
    else:
        tender_id_input = st.text_input("GeM Tender Reference ID:", value=st.session_state.active_tender_id)
    
    st.session_state.active_tender_id = tender_id_input

    # Preview files inside selected tender folder
    existing_files = tender_service.get_tender_files(tender_id_input)
    if existing_files:
        st.markdown(f"**Found {len(existing_files)} document(s) in package `{tender_id_input}`:**")
        for ef in existing_files:
            st.caption(f"- 📄 `{os.path.basename(ef)}` ({os.path.getsize(ef):,} bytes)")

    st.divider()
    st.markdown("### ⚡ Process Tender Package")
    st.write(f"Parse and index all files in package `{tender_id_input}` into ChromaDB.")
    
    if st.button("🚀 Load & Index Selected Tender Package", type="primary", use_container_width=True):
        logger.info(f"Loading tender package folder for ID: {tender_id_input}")
        with st.spinner(f"Indexing tender package '{tender_id_input}' into ChromaDB..."):
            try:
                pkg_res = tender_service.process_tender_package(tender_id_input)
                if pkg_res.get("success"):
                    st.session_state.indexed_files = pkg_res.get("indexed_files", [])
                    st.session_state.tender_indexed = True
                    st.success(f"Indexed {len(st.session_state.indexed_files)} files ({pkg_res.get('total_chunks')} chunks) into ChromaDB for tender '{tender_id_input}'!")
                    logger.info(f"Tender package '{tender_id_input}' indexed successfully.")
                else:
                    st.warning("No valid documents could be indexed from this tender folder.")
            except Exception as e:
                logger.exception(f"Error loading tender package: {e}")
                st.error(f"Failed to load package: {str(e)}")

with col_right:
    st.subheader("2. Upload Documents to Tender Package")
    
    uploaded_files = st.file_uploader(
        "Upload Tender PDF / DOCX / XLSX / CSV Files:",
        type=["pdf", "docx", "xlsx", "xls", "csv", "txt"],
        accept_multiple_files=True
    )
    
    doc_type_selected = st.selectbox(
        "Document Type Category:",
        ["bid_document", "technical_spec", "boq", "corrigendum"]
    )

    if uploaded_files:
        if st.button("Process & Index Uploaded Documents"):
            logger.info(f"Processing {len(uploaded_files)} uploaded tender files for '{tender_id_input}'")
            with st.spinner("Processing & indexing into ChromaDB..."):
                try:
                    clean_id = tender_id_input.replace("/", "_")
                    target_folder = os.path.join("./data/uploads/tender_documents", clean_id)
                    os.makedirs(target_folder, exist_ok=True)
                    
                    for up_file in uploaded_files:
                        save_path = os.path.join(target_folder, up_file.name)
                        with open(save_path, "wb") as f:
                            f.write(up_file.getbuffer())
                        
                        res = tender_service.process_tender_file(
                            file_path=save_path,
                            tender_id=tender_id_input,
                            document_type=doc_type_selected
                        )
                        if res.get("success"):
                            if save_path not in st.session_state.indexed_files:
                                st.session_state.indexed_files.append(save_path)
                            st.session_state.tender_indexed = True
                            st.success(f"Successfully indexed `{up_file.name}` ({res.get('chunks_indexed')} chunks)")
                        else:
                            st.error(f"Failed to process `{up_file.name}`: {res.get('error')}")
                except Exception as e:
                    logger.exception(f"Error processing uploaded files: {e}")
                    st.error(f"Error uploading files: {str(e)}")

    st.divider()
    st.subheader("3. Governing Package Version Register")
    active_files = st.session_state.indexed_files or tender_service.get_tender_files(tender_id_input)
    if active_files:
        doc_rows = []
        for idx, path in enumerate(active_files, 1):
            doc_rows.append({
                "Seq": idx,
                "Source Document": os.path.basename(path),
                "Tender Ref": tender_id_input,
                "Status": "🟢 Confirmed Baseline" if path in st.session_state.indexed_files else "🟡 Package File (Click Index to Load)"
            })
        st.dataframe(doc_rows, use_container_width=True)
    else:
        st.info("No documents currently loaded. Click 'Load & Index Selected Tender Package' or upload files above.")
