"""
Session State Utility - GeM TenderLens.
Provides standardized session state initialization across all Streamlit application pages.
"""

from typing import List, Any


def init_session_state(available_tenders: List[str]) -> None:
    """Initializes all shared Streamlit session_state keys if not already set."""
    import streamlit as st

    if "active_tender_id" not in st.session_state:
        st.session_state["active_tender_id"] = available_tenders[0] if available_tenders else "GEM_9146015"
    if "indexed_files" not in st.session_state:
        st.session_state["indexed_files"] = []
    if "vendor_dossiers" not in st.session_state:
        st.session_state["vendor_dossiers"] = []
    if "comparison_result" not in st.session_state:
        st.session_state["comparison_result"] = None
    if "export_files" not in st.session_state:
        st.session_state["export_files"] = None
    if "tender_indexed" not in st.session_state:
        st.session_state["tender_indexed"] = False
