"""
Export Service for GeM TenderLens.
Generates committee-ready evaluation reports in Markdown, HTML, JSON, and PDF formats.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from utils_logger import get_logger

logger = get_logger(__name__)

EXPORT_DIR = "./data/exports"

class ExportService:
    """Exports structured comparison reports and committee summary packages."""

    def __init__(self):
        self.export_dir = EXPORT_DIR
        os.makedirs(self.export_dir, exist_ok=True)

    def generate_committee_report(
        self,
        tender_id: str,
        comparison_matrix: Dict[str, Any],
        reviewer_notes: str = "",
        sign_off_status: str = "PENDING_APPROVAL"
    ) -> Dict[str, str]:
        """
        Generates markdown, HTML, and JSON report files in `./data/exports`.
        Returns dictionary of generated file paths.
        """
        logger.info(f"Generating committee report export for tender '{tender_id}'")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"Tender_Evaluation_Report_{tender_id.replace('/', '_')}_{timestamp}"

        md_path = os.path.join(self.export_dir, f"{base_filename}.md")
        html_path = os.path.join(self.export_dir, f"{base_filename}.html")
        json_path = os.path.join(self.export_dir, f"{base_filename}.json")

        try:
            # 1. Generate Markdown content
            md_content = self._build_markdown_report(tender_id, comparison_matrix, reviewer_notes, sign_off_status)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            # 2. Generate HTML content
            html_content = self._build_html_report(md_content, tender_id)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # 3. Export raw JSON data
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "tender_id": tender_id,
                    "generated_at": datetime.now().isoformat(),
                    "sign_off_status": sign_off_status,
                    "reviewer_notes": reviewer_notes,
                    "comparison_data": comparison_matrix
                }, f, indent=2, default=str)

            logger.info(f"Report files exported successfully: {md_path}, {html_path}")

            return {
                "markdown": md_path,
                "html": html_path,
                "json": json_path,
                "filename": base_filename
            }

        except Exception as e:
            logger.exception(f"Failed to generate evaluation report: {e}")
            raise

    def _build_markdown_report(
        self,
        tender_id: str,
        matrix: Dict[str, Any],
        reviewer_notes: str,
        sign_off_status: str
    ) -> str:
        """Constructs committee-ready markdown string."""
        commercials = matrix.get("commercial_comparison", [])
        findings = matrix.get("compliance_findings", [])
        risks = matrix.get("risk_queue", [])
        l1_vendor = matrix.get("l1_vendor", "N/A")

        lines = [
            f"# GeM Tender Evaluation Report",
            f"**Tender Reference ID:** `{tender_id}`",
            f"**Generated On:** `{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}`",
            f"**Committee Sign-Off Status:** `{sign_off_status}`",
            f"**Recommended L-1 Vendor:** `{l1_vendor}`",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            f"This evaluation package summarizes the multi-agent comparison of vendor proposals submitted against GeM Tender `{tender_id}`. "
            f"A total of **{matrix.get('total_vendors', 0)}** vendor proposals were analyzed across technical, commercial, and risk dimensions.",
            "",
            "## 2. Commercial Comparison & Price Normalization Table",
            "",
            "| Rank | Vendor Name | Quoted Price (INR) | Tax / GST (INR) | Total Cost (INR) | Delivery (Days) | MSE Status | L-Status |",
            "|---|---|---|---|---|---|---|---|",
        ]

        for c in commercials:
            tax_str = f"₹{c['tax_amount']:,.2f} (18% GST Added)" if c.get('tax_amount', 0) > 0 else "Included in Base Quote"
            lines.append(
                f"| {c['rank']} | **{c['vendor_name']}** | {c['base_price']:,.2f} | {tax_str} | **{c['total_cost']:,.2f}** | {c['delivery_days']} | {c['mse_status']} | **{c['l_status']}** |"
            )

        lines.extend([
            "",
            "## 3. Technical Compliance Matrix",
            "",
            "| Vendor Name | Requirement | Status | Rationale & Evidence | Confidence |",
            "|---|---|---|---|---|",
        ])

        STATUS_BADGES = {
            "compliant": "🟢 COMPLIANT",
            "review_required": "🟡 REVIEW REQUIRED",
            "partial": "🔵 PARTIAL / EXEMPTION"
        }

        for f in findings:
            status_badge = STATUS_BADGES.get(f['status'], "🔴 NON-COMPLIANT")
            lines.append(
                f"| **{f['vendor_name']}** | {f['requirement_name']} | {status_badge} | {f['explanation']} | {f['confidence']*100:.0f}% |"
            )

        lines.extend([
            "",
            "## 4. Risk & Clarification Queue",
            ""
        ])

        if risks:
            for idx, r in enumerate(risks, 1):
                lines.append(f"{idx}. **{r['vendor_name']}** - `{r['issue_type']}`: {r['description']} *(Action: {r['suggested_action']})*")
        else:
            lines.append("No material risks or critical missing documents flagged.")

        lines.extend([
            "",
            "---",
            "",
            "## 5. Reviewer Sign-Off & Approvals",
            f"**Reviewer Notes:** {reviewer_notes or 'No additional notes recorded.'}",
            "",
            "> **Guardrail Notice:** This system provides AI-assisted evaluation support. Final approval, rejection, and tender-award decisions rest entirely with the authorized human procurement committee."
        ])

        return "\n".join(lines)

    def _build_html_report(self, md_content: str, tender_id: str) -> str:
        """Converts Markdown report string to styled standalone HTML document."""
        import html
        escaped_content = html.escape(md_content)
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>GeM Tender Evaluation Report - {tender_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 40px; color: #1e293b; background-color: #f8fafc; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        h1 {{ color: #0f172a; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #1e40af; margin-top: 30px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; border: 1px solid #cbd5e1; text-align: left; }}
        th {{ background-color: #f1f5f9; color: #0f172a; font-weight: 600; }}
        tr:nth-child(even) {{ background-color: #f8fafc; }}
        .badge {{ background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }}
        pre {{ background: #f1f5f9; padding: 15px; border-radius: 6px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <pre>{escaped_content}</pre>
    </div>
</body>
</html>"""
