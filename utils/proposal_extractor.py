"""
Proposal Extractor Utility for GeM TenderLens.
Consolidates regex parsing, price extraction, GST normalization, delivery timelines, and warranty terms.
"""

import re
from schemas.vendor import VendorProposal
from utils.gst_helper import normalize_gst
from utils_logger import get_logger

logger = get_logger(__name__)


def extract_proposal_fields_from_text(vendor_id: str, text: str) -> VendorProposal:
    """Extracts numerical & technical values from text using regex and heuristics."""
    logger.info(f"Extracting proposal fields for vendor '{vendor_id}'")

    # Exclude lines mentioning past orders/experience
    clean_lines = [
        line for line in text.splitlines()
        if not any(past in line.lower() for past in ['past supply', 'prior supply', 'supply order', 'po no', 'past order', 'completion certificate'])
    ]
    clean_text = '\n'.join(clean_lines)
    text_lower = text.lower()

    # 1. Price extraction
    quoted_amount = None
    total_patterns = [
        r'(?:grand\s+total|total\s+amount|quoted\s+amount|final\s+bid)(?:[^\n\d]*)(?:rs\.?|inr|\u20b9)?\s*([0-9,]+(?:\.[0-9]{2})?)',
        r'(?:total|cost)[^\n\d]*(?:rs\.?|inr|\u20b9)?\s*([0-9,]{6,}(?:\.[0-9]{2})?)',
        r'(?:rs\.?|inr|\u20b9)\s*([0-9,]{6,}(?:\.[0-9]{2})?)'
    ]

    for pat in total_patterns:
        matches = re.findall(pat, clean_text, re.IGNORECASE)
        for m in matches:
            try:
                val = float(m.replace(',', ''))
                if val > 1000:
                    quoted_amount = val
                    break
            except ValueError:
                pass
        if quoted_amount:
            break

    # 2. Tax & GST extraction
    is_incl_gst = any(term in text_lower for term in ["incl. gst", "inclusive of gst", "incl gst", "total incl. gst", "total (incl. gst)"])

    tax_amount = 0.0
    if not is_incl_gst and quoted_amount:
        tax_matches = re.findall(r'(?:gst|tax|vat)[:\s]*INR\s*([0-9,]+(?:\.[0-9]{2})?)|(?:gst|tax)[:\s]*([0-9]+)%', text, re.IGNORECASE)
        if tax_matches:
            flat_tax = [t for tup in tax_matches for t in tup if t]
            if flat_tax:
                try:
                    tax_val = float(flat_tax[0].replace(",", ""))
                    tax_amount = round((tax_val / 100.0) * quoted_amount, 2) if tax_val < 100 else tax_val
                except ValueError:
                    tax_amount = 0.0

    tax_amount = normalize_gst(text_lower, quoted_amount or 0.0, tax_amount)

    # 3. Delivery days
    delivery_days = 21
    deliv_patterns = [
        r'(?:delivery\s+(?:timeline|period|lead\s+time)?|deliver)[:\s]*(\d+)\s*(?:days|working days|calendar days)',
        r'(\d+)\s*days\s+(?:for\s+all\s+items|to|delivery)'
    ]
    for dpat in deliv_patterns:
        dmatches = re.findall(dpat, text, re.IGNORECASE)
        if dmatches:
            try:
                delivery_days = int(dmatches[0])
                break
            except ValueError:
                pass

    # 4. Warranty months
    warranty_matches = re.findall(r'(\d+)\s*(months?|years?|yrs?|yr)(?:\s+\w+){0,2}\s*warranty', text, re.IGNORECASE)
    warranty_months = 12
    if warranty_matches:
        try:
            val, unit = int(warranty_matches[0][0]), warranty_matches[0][1].lower()
            warranty_months = val * 12 if unit.startswith("year") or unit.startswith("yr") else val
        except (ValueError, IndexError):
            warranty_months = 12

    # 5. Technical claims & certificates
    claims = []
    if any(term in text_lower for term in ["make", "publisher", "brand", "model"]):
        claims.append("Exact make/model and technical details provided.")
    if any(term in text_lower for term in ["spec", "compliant", "compliance"]):
        claims.append("Fully compliant with tender technical specifications.")
    if "delivery" in text_lower or "consignee" in text_lower:
        claims.append(f"Offered delivery schedule of {delivery_days} days.")

    certs = []
    cert_map = [
        (["udyam", "mse"], "MSE / Udyam Registration Certificate"),
        (["gst", "tax"], "GST Registration Certificate"),
        (["oem", "authorization"], "OEM Authorization Certificate"),
        (["iso", "9001"], "ISO 9001 Quality Certificate"),
        (["non-blacklisting", "blacklisting"], "Self-Declaration of Non-Blacklisting")
    ]
    for terms, cert_name in cert_map:
        if any(term in text_lower for term in terms):
            certs.append(cert_name)

    return VendorProposal(
        vendor_id=vendor_id,
        quoted_amount=quoted_amount,
        currency="INR",
        tax_amount=tax_amount,
        delivery_days=delivery_days,
        warranty_months=warranty_months,
        technical_claims=claims,
        certificates_submitted=certs,
        extraction_confidence=0.95 if quoted_amount else 0.60
    )
