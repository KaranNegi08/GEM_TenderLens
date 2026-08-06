import os
import json
import urllib.request
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

from utils_logger import get_logger

logger = get_logger(__name__)


class VectorEmbeddingProvider:
    """Provides embeddings for ChromaDB vector operations, prioritizing Cohere API Embeddings."""

    def __init__(self, model_name: str = "embed-english-v3.0"):
        self.model_name = os.getenv("COHERE_MODEL", model_name)
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self._model = None

        if self.cohere_api_key and self.cohere_api_key != "COHERE_API_KEY":
            logger.info(f"Configured Cohere API Embeddings (model: '{self.model_name}')")
        else:
            self._initialize_local_model()

    def _initialize_local_model(self):
        """Initializes SentenceTransformer model."""
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Initialized local SentenceTransformer model 'all-MiniLM-L6-v2' successfully.")

    def embed_texts(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """Generates embedding vectors for a list of text strings."""
        if not texts:
            return []

        # 1. Try Cohere API Embeddings if key is configured
        if self.cohere_api_key and self.cohere_api_key != "COHERE_API_KEY":
            try:
                embeddings = self._embed_with_cohere(texts, input_type=input_type)
                if embeddings and len(embeddings) == len(texts):
                    return embeddings
            except Exception as e:
                logger.error(f"Cohere Embedding API error: {e}. Falling back to local embeddings.")

        # 2. Local SentenceTransformer
        if not self._model:
            self._initialize_local_model()

        embeddings = self._model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def _embed_with_cohere(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """Calls Cohere Embeddings API in batches with rate-limit retries."""
        import time

        batch_size = 25
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeds = None

            for attempt in range(5):
                try:
                    url = "https://api.cohere.com/v1/embed"
                    headers = {
                        "Authorization": f"Bearer {self.cohere_api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                    data = json.dumps({
                        "texts": batch,
                        "model": self.model_name,
                        "input_type": input_type
                    }).encode("utf-8")

                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=30) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        embeddings = res_data.get("embeddings", [])
                        if isinstance(embeddings, dict) and "float" in embeddings:
                            batch_embeds = embeddings["float"]
                        elif isinstance(embeddings, list):
                            batch_embeds = embeddings
                    if batch_embeds:
                        break
                except Exception as req_err:
                    if "429" in str(req_err):
                        wait_sec = (attempt + 1) * 3
                        logger.warning(f"Cohere API rate limited (429). Waiting {wait_sec}s (attempt {attempt+1}/5)...")
                        time.sleep(wait_sec)
                    else:
                        logger.error(f"Cohere API batch error: {req_err}")
                        time.sleep(2)

            if not batch_embeds:
                raise RuntimeError("Failed to generate Cohere embeddings for batch after retries")

            all_embeddings.extend(batch_embeds)
            # Small pause between batches to avoid hitting rate limits
            time.sleep(0.5)

        return all_embeddings

