"""
Vendor Comparison Screen - GeM TenderLens.
Executes CrewAI multi-agent workflow to produce technical compliance matrix, commercial cost table, and risk queue.
"""

import streamlit as st
from crew.tender_crew import TenderEvaluationCrew
from utils_logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Vendor Comparison - GeM TenderLens", page_icon="📊", layout="wide")

st.title("📊 Multi-Agent Vendor Proposal Comparison")
st.caption("CrewAI agent workflow evaluates technical compliance, commercial pricing, and risk queues.")

from services.tender_service import TenderService

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

if st.button("🚀 Run Multi-Agent Comparison Crew", type="primary"):
    if not st.session_state.get("vendor_dossiers"):
        st.error("Please load vendor dossiers first in Page 2 (Vendor Intake).")
    else:
        logger.info(f"Triggering multi-agent comparison for tender '{st.session_state.active_tender_id}'")
        with st.spinner("CrewAI agents analyzing technical, commercial, and risk factors..."):
            try:
                crew_runner = TenderEvaluationCrew(st.session_state.active_tender_id)
                doc_list = st.session_state.get("indexed_files", ["GeM_Bid_GEM_2026_B_7798305.txt"])
                res = crew_runner.run_full_evaluation(doc_list, st.session_state.vendor_dossiers)
                st.session_state.comparison_result = res
                st.success("Multi-agent comparison completed successfully!")
            except Exception as e:
                logger.exception(f"Error running comparison crew: {e}")
                st.error(f"Comparison workflow failed: {str(e)}")

st.divider()

if st.session_state.get("comparison_result"):
    res = st.session_state.comparison_result
    financial_l1 = res.get("l1_vendor", "N/A")
    financial_cost = res.get("l1_cost", 0.0)
    dev_count = res.get("l1_deviations_count", 0)
    qualified_l1 = res.get("l1_qualified_vendor", "N/A")
    qualified_cost = res.get("l1_qualified_cost", 0.0)

    if dev_count > 0 and qualified_l1 != financial_l1:
        st.warning(
            f"⚠️ **Lowest Financial Bidder (L-1):** `{financial_l1}` (₹{financial_cost:,.2f} Incl. GST) has **{dev_count} technical/eligibility deviation(s)**. Review required before contract award.\n\n"
            f"🟢 **Recommended Technically Qualified Awardee:** `{qualified_l1}` (₹{qualified_cost:,.2f} Incl. GST) — Passed 100% of technical & documentary checks."
        )
    else:
        st.success(f"🏆 **Recommended L-1 Lowest Qualified Bidder:** `{financial_l1}` (Total Cost: ₹{financial_cost:,.2f} Incl. GST)")

    st.subheader("1. Commercial Price Normalization Table (Incl. GST)")
    commercials = res.get("commercial_comparison", [])
    if commercials:
        rows = []
        for c in commercials:
            rows.append({
                "Rank": c["l_status"],
                "Vendor Name": c["vendor_name"],
                "Quoted Base Price (INR)": f"₹{c['base_price']:,.2f}",
                "GST / Tax Details": c.get("tax_note", f"₹{c['tax_amount']:,.2f}"),
                "Normalized Total Cost (INR)": f"₹{c['total_cost']:,.2f}",
                "Delivery Period": f"{c['delivery_days']} Days",
                "MSE Status": c["mse_status"]
            })
        st.dataframe(rows, use_container_width=True)

    st.subheader("2. Granular Item-Level Technical Compliance Matrix")
    findings = res.get("compliance_findings", [])
    if findings:
        vendor_names = sorted(list(set(f["vendor_name"] for f in findings)))
        filter_vendor = st.selectbox("Filter Compliance Matrix by Vendor:", ["All Bidders"] + vendor_names)
        
        trows = []
        for f in findings:
            if filter_vendor != "All Bidders" and f["vendor_name"] != filter_vendor:
                continue

            if f["status"] == "compliant":
                status_icon = "🟢 Compliant"
            elif f["status"] == "review_required":
                status_icon = "🟡 Review Required"
            elif f["status"] == "partial":
                status_icon = "🔵 Partial / Exemption"
            else:
                status_icon = "🔴 Non-Compliant"

            trows.append({
                "Vendor": f["vendor_name"],
                "Requirement / Item": f["requirement_name"],
                "Status": status_icon,
                "Rationale & Source Evidence": f["explanation"]
            })
        st.dataframe(trows, use_container_width=True)
else:
    st.info("Click 'Run Multi-Agent Comparison Crew' above to execute the evaluation workflow.")
