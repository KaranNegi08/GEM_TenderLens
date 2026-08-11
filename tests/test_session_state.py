"""
Unit test for utils.session_state utility module.
"""

from unittest.mock import MagicMock, patch
from utils.session_state import init_session_state


def test_init_session_state_defaults():
    mock_session_state = {}

    with patch("streamlit.session_state", mock_session_state):
        init_session_state(["GEM_12345"])

        assert mock_session_state["active_tender_id"] == "GEM_12345"
        assert mock_session_state["indexed_files"] == []
        assert mock_session_state["vendor_dossiers"] == []
        assert mock_session_state["comparison_result"] is None
        assert mock_session_state["export_files"] is None
        assert mock_session_state["tender_indexed"] is False


def test_init_session_state_preserves_existing():
    mock_session_state = {
        "active_tender_id": "EXISTING_TENDER",
        "tender_indexed": True
    }

    with patch("streamlit.session_state", mock_session_state):
        init_session_state(["GEM_12345"])

        assert mock_session_state["active_tender_id"] == "EXISTING_TENDER"
        assert mock_session_state["tender_indexed"] is True
        assert mock_session_state["indexed_files"] == []
