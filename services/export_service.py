"""
Export Service for GeM TenderLens.
Generates committee-ready evaluation reports in Markdown, HTML, JSON, and PDF formats.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.status_badges import get_status_badge
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
    ) -> Dict[str, Any]:
        """
        Generates markdown, HTML, JSON, and PDF report files in `./data/exports`.
        Returns dictionary of generated file paths.
        """
        logger.info(f"Generating committee report export for tender '{tender_id}'")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"Tender_Evaluation_Report_{tender_id.replace('/', '_')}_{timestamp}"

        md_path = os.path.join(self.export_dir, f"{base_filename}.md")
        html_path = os.path.join(self.export_dir, f"{base_filename}.html")
        json_path = os.path.join(self.export_dir, f"{base_filename}.json")
        pdf_path = os.path.join(self.export_dir, f"{base_filename}.pdf")

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

            # 4. Generate PDF report (Issue #1 fix)
            pdf_export_path: Optional[str] = None
            try:
                self._build_pdf_report(md_content, pdf_path)
                pdf_export_path = pdf_path
            except Exception as pdf_err:
                logger.warning(f"PDF generation failed, continuing with MD/HTML/JSON: {pdf_err}")
                pdf_export_path = None

            logger.info(f"Report files exported successfully: {md_path}, {html_path}, {pdf_export_path}")

            return {
                "markdown": md_path,
                "html": html_path,
                "json": json_path,
                "pdf": pdf_export_path,
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

        # Issue #3 fix: Header L-1 details
        l1_vendor = matrix.get("l1_vendor", "N/A")
        l1_cost = matrix.get("l1_cost", 0.0)
        l1_qual_vendor = matrix.get("l1_qualified_vendor", "N/A")
        l1_qual_cost = matrix.get("l1_qualified_cost", 0.0)
        l1_deviations = matrix.get("l1_deviations_count", 0)

        lines = [
            f"# GeM Tender Evaluation Report",
            f"**Tender Reference ID:** `{tender_id}`",
            f"**Generated On:** `{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}`",
            f"**Committee Sign-Off Status:** `{sign_off_status}`",
            f"**Financial L-1 Vendor:** `{l1_vendor}` (Cost: ₹{l1_cost:,.2f})",
            f"**Technically-Qualified L-1 Vendor:** `{l1_qual_vendor}` (Cost: ₹{l1_qual_cost:,.2f})",
        ]

        if l1_deviations > 0 or (l1_vendor != l1_qual_vendor and l1_qual_vendor != "N/A"):
            lines.append(f"⚠️ **Note:** Financial L-1 vendor has {l1_deviations} compliance deviation(s). Review Technical Compliance Matrix before award.")

        lines.extend([
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
        ])

        for c in commercials:
            # Issue #2 fix: Use c['tax_note'] directly instead of duplicating tax_str calculation
            tax_note = c.get('tax_note', 'N/A')
            lines.append(
                f"| {c['rank']} | **{c['vendor_name']}** | {c['base_price']:,.2f} | {tax_note} | **{c['total_cost']:,.2f}** | {c['delivery_days']} | {c['mse_status']} | **{c['l_status']}** |"
            )

        lines.extend([
            "",
            "## 3. Technical Compliance Matrix",
            "",
            "| Vendor Name | Requirement | Status | Rationale & Evidence | Confidence |",
            "|---|---|---|---|---|",
        ])

        for f in findings:
            status_badge = get_status_badge(f['status'], upper=True)
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
        # Issue #5 fix: Use markdown library for actual HTML parsing & rendering
        try:
            import markdown
            html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        except Exception:
            import html
            html_body = f"<pre>{html.escape(md_content)}</pre>"

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
        code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }}
        blockquote {{ background: #eff6ff; border-left: 4px solid #2563eb; margin: 0; padding: 12px 16px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-content">
            {html_body}
        </div>
    </div>
</body>
</html>"""

    def _build_pdf_report(self, md_content: str, pdf_path: str) -> None:
        """Converts Markdown report string into a styled PDF document using ReportLab."""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        normal_style = styles["Normal"]

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=8
        )

        h2_style = ParagraphStyle(
            'ReportH2',
            parent=styles['Heading2'],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#1e40af'),
            spaceBefore=10,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=normal_style,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=3
        )

        story = []
        lines = md_content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line == "---":
                story.append(Spacer(1, 4))
                i += 1
                continue

            if line.startswith("# "):
                title_text = line[2:].strip()
                story.append(Paragraph(title_text, title_style))
            elif line.startswith("## "):
                h2_text = line[3:].strip()
                story.append(Paragraph(h2_text, h2_style))
            elif line.startswith("|") and "|" in line[1:]:
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    tline = lines[i].strip()
                    if not tline.replace("|", "").replace("-", "").strip() == "":
                        table_lines.append(tline)
                    i += 1

                if table_lines:
                    table_data = []
                    for tl in table_lines:
                        cells = [c.strip().replace("**", "") for c in tl.split("|")[1:-1]]
                        row_cells = [Paragraph(cell, body_style) for cell in cells]
                        table_data.append(row_cells)

                    if table_data:
                        t = Table(table_data)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                            ('TOPPADDING', (0, 0), (-1, -1), 3),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 6))
                continue
            else:
                formatted_line = line
                while "**" in formatted_line and formatted_line.count("**") >= 2:
                    formatted_line = formatted_line.replace("**", "<b>", 1)
                    formatted_line = formatted_line.replace("**", "</b>", 1)
                while "`" in formatted_line and formatted_line.count("`") >= 2:
                    formatted_line = formatted_line.replace("`", "<font name='Courier'>", 1)
                    formatted_line = formatted_line.replace("`", "</font>", 1)
                # Clean up any leftover single backticks or markdown markers safely
                formatted_line = formatted_line.replace("`", "")
                story.append(Paragraph(formatted_line, body_style))

            i += 1

        doc.build(story)
        logger.info(f"PDF report successfully created at '{pdf_path}'")
