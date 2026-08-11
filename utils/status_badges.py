"""
Status badges helper module for GeM TenderLens.
Consolidates vendor compliance status badge mapping across UI and Export services.
"""

STATUS_BADGES = {
    "compliant": "🟢 Compliant",
    "review_required": "🟡 Review Required",
    "partial": "🔵 Partial / Exemption",
    "non_compliant": "🔴 Non-Compliant"
}


def get_status_badge(status: str, upper: bool = False) -> str:
    """Returns standardized status icon badge string. Optional upper=True for uppercase report exports."""
    badge = STATUS_BADGES.get(status, "⚪ Unknown Status")
    return badge.upper() if upper else badge
