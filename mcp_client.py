"""
Model Context Protocol (MCP) Client Interface for GeM TenderLens.
Enables standard JSON-RPC 2.0 communication with an MCP Server instance.
"""

import json
from typing import Dict, Any, List, Optional
from mcp_server import MCPServer
from utils_logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """
    Model Context Protocol (MCP) Client Implementation.
    Formulates JSON-RPC 2.0 standard requests to discover tools, execute functions, and read resources.
    """

    def __init__(self, server: Optional[MCPServer] = None):
        self.server = server or MCPServer()

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None, req_id: int = 1) -> Dict[str, Any]:
        """Dispatches a JSON-RPC 2.0 request payload to the MCP Server."""
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }
        raw_response = self.server.handle_json_rpc(json.dumps(payload))
        response = json.loads(raw_response)

        if "error" in response:
            logger.error(f"MCP Client received error response: {response['error']}")
            raise RuntimeError(f"MCP Error ({response['error']['code']}): {response['error']['message']}")

        return response.get("result", {})

    def list_tools(self) -> List[Dict[str, Any]]:
        """Queries the MCP server for all registered tool schemas."""
        res = self._send_request("tools/list")
        return res.get("tools", [])

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invokes an MCP tool by name with specified input arguments."""
        res = self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
        return res

    def list_resources(self) -> List[Dict[str, Any]]:
        """Queries the MCP server for available resources."""
        res = self._send_request("resources/list")
        return res.get("resources", [])

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Reads a resource by URI from the MCP server."""
        return self._send_request("resources/read", {"uri": uri})


if __name__ == "__main__":
    client = MCPClient()
    print("Testing MCP Client...")
    tools = client.list_tools()
    print(f"Discovered {len(tools)} tools via MCP JSON-RPC protocol:")
    for t in tools:
        print(f"  - {t['name']}")
