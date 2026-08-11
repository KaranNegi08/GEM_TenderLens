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

# 0. Per-Finding Committee Review Section
st.subheader("0. Per-Finding Committee Review")
if st.session_state.get("comparison_result"):
    findings = st.session_state.comparison_result.get("compliance_findings", [])
    if findings:
        vendor_names = sorted(list(set(f["vendor_name"] for f in findings)))
        for v_name in vendor_names:
            with st.expander(f"📋 {v_name} — Findings Review", expanded=False):
                vendor_findings = [f for f in findings if f["vendor_name"] == v_name]
                for f in vendor_findings:
                    finding_key = f"{f['vendor_id']}:{f['requirement_id']}"
                    col_f1, col_f2, col_f3 = st.columns([2, 1, 2])
                    with col_f1:
                        st.write(f"**{f['requirement_name']}**")
                        st.caption(f['explanation'])
                    with col_f2:
                        review_status = st.selectbox(
                            "Review Status",
                            ["pending", "approved", "rejected", "clarification_needed"],
                            key=f"review_status_{finding_key}",
                            label_visibility="collapsed"
                        )
                    with col_f3:
                        review_comment = st.text_input(
                            "Comment",
                            key=f"review_comment_{finding_key}",
                            placeholder="Optional reviewer comment...",
                            label_visibility="collapsed"
                        )

        if st.button("💾 Save All Finding Reviews"):
            try:
                from services.audit_service import DatabaseAuditService
                from schemas.audit import ReviewerAction
                saved_count = 0
                for f in findings:
                    finding_key = f"{f['vendor_id']}:{f['requirement_id']}"
                    status_key = f"review_status_{finding_key}"
                    comment_key = f"review_comment_{finding_key}"
                    if status_key in st.session_state and st.session_state[status_key] != "pending":
                        action_obj = ReviewerAction(
                            finding_id=finding_key,
                            action=st.session_state[status_key],
                            reviewer_comments=st.session_state.get(comment_key, "")
                        )
                        DatabaseAuditService.save_reviewer_action(action_obj)
                        saved_count += 1
                st.success(f"Saved {saved_count} finding-level review(s).")
            except Exception as e:
                logger.exception(f"Error saving finding reviews: {e}")
                st.error(f"Failed to save reviews: {str(e)}")
    else:
        st.info("No compliance findings available yet.")
else:
    st.info("Run comparison in Page 4 first to review individual findings.")

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Procurement Committee Sign-Off")
    status_opt = st.selectbox("Sign-Off Approval Status:", ["APPROVED_RECOMMENDED_FOR_AWARD", "CLARIFICATIONS_REQUESTED", "REJECTED_RE_TENDER_REQUIRED"])
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

                # Audit Log & Reviewer Action persistence
                try:
                    from services.audit_service import DatabaseAuditService
                    from schemas.audit import ReviewerAction, AuditLog
                    import uuid

                    action_obj = ReviewerAction(
                        finding_id=f"TENDER_SIGNOFF_{st.session_state.active_tender_id}",
                        action=status_opt,
                        reviewer_comments=notes
                    )
                    DatabaseAuditService.save_reviewer_action(action_obj)

                    audit_log = AuditLog(
                        log_id=f"AUDIT_{uuid.uuid4().hex[:12].upper()}",
                        actor="HumanReviewer",
                        action_type="COMMITTEE_SIGNOFF",
                        details={
                            "tender_id": st.session_state.active_tender_id,
                            "sign_off_status": status_opt,
                            "notes_recorded": bool(notes)
                        }
                    )
                    DatabaseAuditService.save_audit_log(audit_log)
                except Exception as audit_err:
                    logger.warning(f"Could not save reviewer action audit log: {audit_err}")

                st.success("Report package generated and committee sign-off recorded!")
            except Exception as e:
                logger.exception(f"Error exporting report: {e}")
                st.error(f"Export failed: {str(e)}")

with col2:
    if st.session_state.get("export_files"):
        files = st.session_state.export_files
        st.subheader("2. Download Reports")
        if files.get("markdown") and os.path.exists(files["markdown"]):
            with open(files["markdown"], "r", encoding="utf-8") as f:
                st.download_button("Download Markdown Report (.md)", data=f.read(), file_name=os.path.basename(files["markdown"]), mime="text/markdown")
        if files.get("html") and os.path.exists(files["html"]):
            with open(files["html"], "r", encoding="utf-8") as f:
                st.download_button("Download HTML Package (.html)", data=f.read(), file_name=os.path.basename(files["html"]), mime="text/html")
        if files.get("json") and os.path.exists(files["json"]):
            with open(files["json"], "r", encoding="utf-8") as f:
                st.download_button("Download Raw JSON Data (.json)", data=f.read(), file_name=os.path.basename(files["json"]), mime="application/json")
        if files.get("pdf") and os.path.exists(files["pdf"]):
            with open(files["pdf"], "rb") as f:
                st.download_button("Download PDF Report (.pdf)", data=f.read(), file_name=os.path.basename(files["pdf"]), mime="application/pdf")

st.divider()

if st.session_state.get("export_files") and st.session_state.export_files.get("markdown") and os.path.exists(st.session_state.export_files["markdown"]):
    st.subheader("3. Report Preview")
    with open(st.session_state.export_files["markdown"], "r", encoding="utf-8") as f:
        st.markdown(f.read())
