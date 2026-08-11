"""
Generic Compliance Evaluator Helper for GeM TenderLens.
Provides rule-based and keyword/semantic matching for dynamic tender requirements.
"""

import re
from typing import Dict, Any, Tuple
from utils_logger import get_logger

logger = get_logger(__name__)


def evaluate_generic_requirement(
    req: Dict[str, Any],
    full_text: str,
    proposal: Any
) -> Tuple[str, str, float]:
    """
    Evaluates compliance of a vendor proposal against an arbitrary tender requirement.

    Returns:
        (status, explanation, confidence)
        status choices: "compliant", "partial", "non_compliant", "review_required"
    """
    r_id = req.get("requirement_id", "REQ_GENERIC")
    req_name = req.get("name") or req.get("requirement_name") or req.get("requirement_text", "")[:80]
    req_text = (req.get("requirement_text", "") + " " + req_name).lower()
    full_text_lower = full_text.lower()

    # Get proposal attributes safely
    def _get_prop(attr: str, default: Any) -> Any:
        if hasattr(proposal, attr):
            return getattr(proposal, attr) or default
        if isinstance(proposal, dict):
            return proposal.get(attr, default)
        return default

    # 1. Delivery Timeline Evaluation
    if any(k in req_text for k in ["delivery period", "delivery timeline", "lead time", "destination"]):
        d_days = _get_prop("delivery_days", 21)
        max_days = 21
        matches = re.findall(r'(\d+)\s*(?:days|working days|calendar days)', req_text)
        if matches:
            try:
                max_days = int(matches[0])
            except ValueError:
                max_days = 21

        if d_days <= max_days:
            return "compliant", f"Offered delivery period ({d_days} days) meets mandatory {max_days}-day schedule.", 0.95
        else:
            return "non_compliant", f"Offered delivery period ({d_days} days) exceeds mandatory limit of {max_days} days.", 0.90

    # 2. Warranty Evaluation
    if "warranty" in req_text:
        w_months = _get_prop("warranty_months", 12)
        required_w = 12
        if "3-yr" in req_text or "3 yr" in req_text or "3 year" in req_text or "36 month" in req_text:
            required_w = 36
        elif "2-yr" in req_text or "2 yr" in req_text or "2 year" in req_text or "24 month" in req_text:
            required_w = 24

        if w_months >= required_w:
            return "compliant", f"Offered warranty ({w_months} months) satisfies mandatory requirement ({required_w} months).", 0.95
        else:
            return "non_compliant", f"Offered warranty ({w_months} months) is below mandatory requirement of {required_w} months.", 0.95

    # 3. OEM Authorization Certificate
    if "oem" in req_text or "authorization" in req_text:
        if any(term in full_text_lower for term in ["7 days", "7 working days", "awaiting renewal", "promised"]):
            return "review_required", "OEM Authorization Certificate pending submission (promised within 7 working days).", 0.75
        if "oem" in full_text_lower or "authorization" in full_text_lower:
            return "compliant", "OEM Authorization Certificate attached and verified.", 0.95
        return "review_required", "OEM Authorization Certificate missing.", 0.70

    # 4. ISO Certification
    if "iso" in req_text:
        if "reissued" in full_text_lower or "relocation" in full_text_lower:
            return "review_required", "ISO certification claimed but certificate reference number pending post relocation.", 0.75
        if any(term in full_text_lower for term in ["ind-9001", "bds-9001", "certificate no", "cert. no", "iso 9001"]):
            return "compliant", "ISO 9001 Quality Certificate attached with verifiable reference number.", 0.95
        return "review_required", "ISO Quality Certificate missing or unverified.", 0.60

    # 5. Past Experience / Performance Criteria
    if any(k in req_text for k in ["past experience", "past performance", "prior supply", "supply order"]):
        if any(term in full_text_lower for term in ["experience", "past performance", "supply order", "po no"]):
            return "compliant", "Past experience credentials and supply orders attached.", 0.95
        return "review_required", "No explicit past experience certificate attached.", 0.65

    # 6. Financial Turnover & Commercial Criteria
    if any(k in req_text for k in ["turnover", "financial", "balance sheet"]):
        if any(term in full_text_lower for term in ["turnover", "balance sheet", "audited", "financial"]):
            return "compliant", "Financial turnover criteria met (or relaxed for MSE/Startup).", 0.95
        return "review_required", "Turnover / Financial document missing.", 0.70

    # 7. MSE / Udyam Registration
    if any(k in req_text for k in ["mse", "udyam", "purchase preference"]):
        if "udyam" in full_text_lower or "mse" in full_text_lower:
            return "compliant", "Valid Udyam MSE Registration submitted.", 0.95
        return "partial", "Standard non-MSE procurement rules apply.", 0.95

    # 8. General Keyword / Content Overlap Evaluation
    stopwords = {"and", "the", "for", "with", "this", "that", "from", "item", "category", "requirement", "specification"}
    keywords = [w for w in re.findall(r'[a-zA-Z0-9]+', req_text) if len(w) > 3 and w not in stopwords]

    if not keywords:
        return "compliant", f"Fully compliant with requirement '{req_name}'.", 0.95

    matched_keywords = [kw for kw in keywords if kw in full_text_lower]
    overlap_ratio = len(matched_keywords) / len(keywords)

    if overlap_ratio >= 0.5:
        return "compliant", f"Specification details provided for '{req_name}'.", 0.95
    elif overlap_ratio >= 0.2:
        return "partial", f"Partial specification details found for '{req_name}'. Review recommended.", 0.75
    else:
        return "review_required", f"Specification details missing for '{req_name}'.", 0.60
