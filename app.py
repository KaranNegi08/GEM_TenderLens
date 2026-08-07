"""
GeM TenderLens - Multi-Agent Tender Proposal Comparison System
Main Landing Page.
"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

from utils_logger import get_logger

logger = get_logger(__name__)


# Streamlit Page Config
st.set_page_config(
    page_title="GeM TenderLens",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from services.database import init_db
from services.tender_service import TenderService

# Initialize database schema tables
init_db()

tender_service = TenderService()
available_tenders = tender_service.list_available_tenders()

# Initialize Standardized Session State Variables
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

logger.info("Main landing page loaded.")

# Sidebar Controls & Navigation
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/security-pass.png", width=60)
    st.title("GeM TenderLens")
    st.caption("Multi-Agent Procurement System")
    
    st.divider()
    
    st.markdown("### ⚙️ Tender Controls")
    if available_tenders:
        selected_tender = st.selectbox(
            "Active Tender Package:",
            options=available_tenders,
            index=available_tenders.index(st.session_state.active_tender_id) if st.session_state.active_tender_id in available_tenders else 0
        )
        st.session_state.active_tender_id = selected_tender
    else:
        tender_id_input = st.text_input("Active Tender ID:", value=st.session_state.active_tender_id)
        st.session_state.active_tender_id = tender_id_input

    st.divider()

    st.markdown("### 📌 Navigation Pages")
    st.page_link("pages/1_tender_workspace.py", label="1. Tender Workspace", icon="📂")
    st.page_link("pages/2_vendor_intake.py", label="2. Vendor Intake", icon="📥")
    st.page_link("pages/3_rag_search.py", label="3. Tender RAG Search", icon="🔍")
    st.page_link("pages/4_vendor_comparison.py", label="4. Vendor Comparison", icon="📊")
    st.page_link("pages/5_review_export.py", label="5. Review & Export", icon="📝")

    st.divider()
    st.markdown("**Status Overview:**")
    st.write(f"- Tender Files: **{len(st.session_state.indexed_files)}**")
    st.write(f"- Vendor Dossiers: **{len(st.session_state.vendor_dossiers)}**")

# Minimal Main Page - Project Title Only & Welcome Banner
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 40px; border-radius: 15px; border: 1px solid #334155; text-align: center; margin-top: 20px;">
        <h1 style="color: #38bdf8; font-size: 3rem; margin-bottom: 10px;">GeM TenderLens</h1>
        <p style="color: #94a3b8; font-size: 1.3rem; margin: 0;">Multi-Agent Tender Proposal Comparison System</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Use the sidebar navigation menu to access **Tender Workspace**, **Vendor Intake**, **RAG Search**, **Vendor Comparison**, and **Review & Export**.")
