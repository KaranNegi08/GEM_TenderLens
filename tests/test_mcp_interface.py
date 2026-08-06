"""
Unit tests for Model Context Protocol (MCP) Server and Client integration.
"""

from mcp_server import MCPServer
from mcp_client import MCPClient


def test_mcp_server_tool_definitions():
    server = MCPServer()
    tools = server.get_tool_definitions()
    tool_names = [t["name"] for t in tools]

    assert "vector_search" in tool_names
    assert "extract_proposal" in tool_names
    assert "parse_vendor_email" in tool_names
    assert "list_tenders" in tool_names


def test_mcp_client_tool_invocation():
    client = MCPClient()

    # 1. Test listing tools
    tools = client.list_tools()
    assert len(tools) >= 4

    # 2. Test extract_proposal tool via MCP JSON-RPC
    sample_text = "Vendor quoted Rs. 500,000 for 50 laptops with 21 days delivery timeline and 3 years warranty."
    res = client.invoke_tool("extract_proposal", {"text_content": sample_text})

    assert res["success"] is True
    content = res["content"]
    assert content["quoted_amount"] == 500000.0
    assert content["delivery_days"] == 21


def test_mcp_resources():
    client = MCPClient()
    resources = client.list_resources()
    assert isinstance(resources, list)
