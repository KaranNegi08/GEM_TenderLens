"""
ChromaDB Persistent Client Manager.
Maintains isolated collections for each tender workspace.
"""

import os
import re
from typing import Optional, List, Dict, Any
import chromadb
from utils_logger import get_logger

logger = get_logger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
_shared_clients: Dict[str, Any] = {}


class ChromaDBClientManager:
    """Manages persistent ChromaDB vector storage with collection isolation per tender."""

    def __init__(self, persist_directory: str = CHROMA_PATH):
        global _shared_clients
        self.persist_directory = os.path.abspath(persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        
        if self.persist_directory not in _shared_clients:
            try:
                _shared_clients[self.persist_directory] = chromadb.PersistentClient(path=self.persist_directory)
                logger.info(f"Initialized ChromaDB persistent client at: {self.persist_directory}")
            except BaseException as client_err:
                logger.warning(f"Could not create PersistentClient for path '{self.persist_directory}' ({client_err}). Using fallback client.")
                if _shared_clients:
                    _shared_clients[self.persist_directory] = list(_shared_clients.values())[0]
                else:
                    _shared_clients[self.persist_directory] = chromadb.EphemeralClient()
        
        self.client = _shared_clients[self.persist_directory]

    def _sanitize_collection_name(self, tender_id: str) -> str:
        """Converts tender_id e.g. GEM/2026/B/7798305 to valid Chroma collection name."""
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', tender_id).lower()
        if len(sanitized) < 3:
            sanitized = f"collection_{sanitized}"
        if len(sanitized) > 63:
            sanitized = sanitized[:63]
        return f"tender_{sanitized}"

    def get_or_create_collection(self, tender_id: str):
        """Retrieves or initializes an isolated ChromaDB collection for a given tender_id."""
        collection_name = self._sanitize_collection_name(tender_id)
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"tender_id": tender_id, "hnsw:space": "cosine"}
            )
            logger.info(f"Retrieved Chroma collection '{collection_name}' for tender_id '{tender_id}'")
            return collection
        except Exception as e:
            logger.exception(f"Failed to get/create Chroma collection for tender '{tender_id}': {e}")
            raise

    def reset_collection(self, tender_id: str) -> bool:
        """Deletes and recreates the collection for a tender workspace."""
        collection_name = self._sanitize_collection_name(tender_id)
        try:
            try:
                self.client.delete_collection(name=collection_name)
                logger.info(f"Deleted collection '{collection_name}' for reset")
            except Exception:
                pass
            self.get_or_create_collection(tender_id)
            return True
        except Exception as e:
            logger.exception(f"Error resetting collection for tender '{tender_id}': {e}")
            return False

    def list_collections(self) -> List[str]:
        """Lists all existing tender collection names."""
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Error listing Chroma collections: {e}")
            return []
