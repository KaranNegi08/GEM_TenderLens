"""
Model Context Protocol (MCP) Server Interface for GeM TenderLens.
Provides standardized JSON-RPC 2.0 function calling and resource access across vector search, document parsers, and vendor email tools.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from rag.retriever import KnowledgeRetriever
from rag.document_loader import DocumentLoader
from services.vendor_service import VendorService
from services.tender_service import TenderService
from utils_logger import get_logger

logger = get_logger(__name__)


class MCPServer:
    """
    Model Context Protocol (MCP) Server Implementation.
    Exposes standardized MCP endpoints:
      - tools/list: List all available MCP tools and parameters
      - tools/call: Invoke an MCP tool by name
      - resources/list: List tender packages and dossiers as MCP resources
      - resources/read: Read content of an MCP resource
    """

    def __init__(self):
        self.retriever = KnowledgeRetriever()
        self.vendor_service = VendorService()
        self.tender_service = TenderService()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns MCP tool definitions matching standard Model Context Protocol schema."""
        return [
            {
                "name": "vector_search",
                "description": "Searches ChromaDB vector knowledge base for GeM tender clauses and requirement evidence.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tender_id": {"type": "string", "description": "GeM Tender Reference ID"},
                        "query": {"type": "string", "description": "Natural language clause or requirement query"},
                        "n_results": {"type": "integer", "default": 3, "description": "Number of top matching clauses to return"}
                    },
                    "required": ["tender_id", "query"]
                }
            },
            {
                "name": "extract_proposal",
                "description": "Extracts financial quote, delivery timeline, warranty, and technical claims from vendor proposal text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text_content": {"type": "string", "description": "Raw text content of the vendor proposal document"}
                    },
                    "required": ["text_content"]
                }
            },
            {
                "name": "parse_vendor_email",
                "description": "Parses vendor email (.eml) or proposal submission files and creates a structured vendor dossier.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vendor_name": {"type": "string", "description": "Vendor company name"},
                        "tender_id": {"type": "string", "description": "GeM Tender ID"},
                        "file_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of proposal file paths to ingest"
                        }
                    },
                    "required": ["vendor_name", "tender_id", "file_paths"]
                }
            },
            {
                "name": "list_tenders",
                "description": "Lists all active tender packages currently indexed in GeM TenderLens.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an MCP tool call to the appropriate internal service."""
        logger.info(f"MCP Server calling tool '{name}' with arguments: {arguments}")

        try:
            if name == "vector_search":
                tender_id = arguments.get("tender_id", "")
                query = arguments.get("query", "")
                n_results = int(arguments.get("n_results", 3))
                results = self.retriever.search_tender_knowledge(tender_id, query, n_results=n_results)
                return {"success": True, "tool": name, "content": results}

            elif name == "extract_proposal":
                text_content = arguments.get("text_content", "")
                proposal = self.vendor_service._extract_proposal_fields("MCP_VENDOR", text_content)
                return {
                    "success": True,
                    "tool": name,
                    "content": {
                        "quoted_amount": proposal.quoted_amount,
                        "currency": proposal.currency,
                        "tax_amount": proposal.tax_amount,
                        "delivery_days": proposal.delivery_days,
                        "warranty_months": proposal.warranty_months,
                        "technical_claims": proposal.technical_claims,
                        "certificates_submitted": proposal.certificates_submitted
                    }
                }

            elif name == "parse_vendor_email":
                vendor_name = arguments.get("vendor_name", "")
                tender_id = arguments.get("tender_id", "")
                file_paths = arguments.get("file_paths", [])
                res = self.vendor_service.process_vendor_submission(vendor_name, tender_id, file_paths)
                return {"success": True, "tool": name, "content": res}

            elif name == "list_tenders":
                tenders = self.tender_service.list_available_tenders()
                return {"success": True, "tool": name, "content": tenders}

            else:
                return {"success": False, "error": f"Unknown MCP tool: '{name}'"}

        except Exception as e:
            logger.exception(f"Error executing MCP tool '{name}': {e}")
            return {"success": False, "error": str(e)}

    def list_resources(self) -> List[Dict[str, Any]]:
        """Lists MCP resources exposed by the server."""
        available_tenders = self.tender_service.list_available_tenders()
        resources = []
        for t_id in available_tenders:
            resources.append({
                "uri": f"tender://{t_id}",
                "name": f"Tender Package: {t_id}",
                "mimeType": "application/json",
                "description": f"Governing document package for tender {t_id}"
            })
        return resources

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Reads content for a specified MCP resource URI."""
        if uri.startswith("tender://"):
            t_id = uri.replace("tender://", "")
            files = self.tender_service.get_tender_files(t_id)
            return {
                "uri": uri,
                "tender_id": t_id,
                "file_count": len(files),
                "files": [os.path.basename(f) for f in files]
            }
        return {"error": f"Resource URI '{uri}' not found."}

    def handle_json_rpc(self, request_json: str) -> str:
        """Processes a JSON-RPC 2.0 formatted MCP request string."""
        try:
            req = json.loads(request_json)
            req_id = req.get("id", 1)
            method = req.get("method", "")
            params = req.get("params", {})

            if method == "tools/list":
                result = {"tools": self.get_tool_definitions()}
            elif method == "tools/call":
                name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = self.call_tool(name, arguments)
            elif method == "resources/list":
                result = {"resources": self.list_resources()}
            elif method == "resources/read":
                uri = params.get("uri", "")
                result = self.read_resource(uri)
            else:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not found."}
                })

            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            })


if __name__ == "__main__":
    server = MCPServer()
    print("GeM TenderLens MCP Server initialized.")
    tools = server.get_tool_definitions()
    print(f"Registered {len(tools)} MCP tools:")
    for t in tools:
        print(f"  - {t['name']}: {t['description']}")
