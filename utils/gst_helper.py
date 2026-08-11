"""
GST Helper Utility for GeM TenderLens.
Provides shared GST detection and tax normalization logic across services.
"""

BEFORE_GST_KEYWORDS = [
    "before gst",
    "excl. gst",
    "excluding gst",
    "+18% gst",
    "+ 18% gst",
    "excl gst",
    "grand total before gst"
]


def normalize_gst(text_lower: str, base_amount: float, existing_tax: float = 0.0) -> float:
    """Detects GST-exclusive language and calculates 18% GST if needed."""
    if not base_amount or base_amount <= 0:
        return existing_tax or 0.0

    is_before_gst = any(term in text_lower for term in BEFORE_GST_KEYWORDS)
    if is_before_gst:
        return round(0.18 * base_amount, 2)

    return existing_tax or 0.0
