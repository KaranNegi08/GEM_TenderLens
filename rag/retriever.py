"""
Retriever Module for GeM TenderLens.

Responsible for:
1. Querying Tender-specific Chroma collections
2. Applying metadata filters
3. Returning evidence citations
4. Preparing context for AI agents
"""

import os
import re
import json
import urllib.request
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from rag.chroma_client import ChromaDBClientManager
from rag.embeddings import VectorEmbeddingProvider
from schemas.evaluation import EvidenceCitation
from utils_logger import get_logger

logger = get_logger(__name__)

from langsmith import traceable


class KnowledgeRetriever:
    """
    Semantic Retrieval Layer for GeM TenderLens.
    
    Collection Isolation:
        Each tender package gets its own vector collection (`tender_<ID>`).
        This prevents cross-tender data contamination during RAG search.

    Search Pipeline (3 Steps):
        1. Vector Query: Search ChromaDB for vector matches.
        2. Keyword Re-Ranking: Boost matching terms and corrigenda.
        3. Citation Assembly: Attach page numbers and source filenames.
    """

    def __init__(self, chroma_manager: Optional[ChromaDBClientManager] = None):
        self.chroma_manager = chroma_manager or ChromaDBClientManager()
        self.embedding_provider = VectorEmbeddingProvider()

    @traceable(name="RAG Knowledge Search")
    def search_tender_knowledge(
        self,
        tender_id: str,
        query: str,
        n_results: int = 5,
        mandatory_only: bool = False,
        document_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from a tender with hybrid keyword re-ranking."""
        logger.info(f"Searching tender={tender_id} | query='{query}'")

        try:
            collection = self.chroma_manager.get_or_create_collection(tender_id)
            collection_size = collection.count()

            if collection_size == 0:
                logger.warning(f"Collection empty for tender {tender_id}")
                return []

            query_embedding = self.embedding_provider.embed_texts([query])[0]

            where_filter = {}
            if mandatory_only:
                where_filter["mandatory_flag"] = True
            if document_type:
                where_filter["document_type"] = document_type

            n_candidates = min(max(25, n_results * 5), collection_size)
            query_args = {
                "query_embeddings": [query_embedding],
                "n_results": n_candidates
            }
            if where_filter:
                query_args["where"] = where_filter

            results = collection.query(**query_args)
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            # Dual-Source Query Routing: If querying generally, also query vendor proposal chunks explicitly
            if not document_type:
                try:
                    v_res = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=min(15, collection_size),
                        where={"document_type": "vendor_proposal"}
                    )
                    v_docs = v_res.get("documents", [[]])[0]
                    v_metas = v_res.get("metadatas", [[]])[0]
                    v_dists = v_res.get("distances", [[]])[0]

                    seen_texts = set(documents)
                    for vd, vm, vdist in zip(v_docs, v_metas, v_dists):
                        if vd not in seen_texts:
                            documents.append(vd)
                            metadatas.append(vm)
                            distances.append(vdist)
                            seen_texts.add(vd)
                except Exception as v_err:
                    logger.debug(f"Dual-source query notice: {v_err}")

            stop_words = {
                "what", "is", "the", "for", "and", "are", "of", "in", "to", "a", "an",
                "this", "that", "it", "with", "or", "by", "has", "any", "been", "affected",
                "recent", "does", "did", "how", "why", "which", "about", "from", "on"
            }
            q_terms = set(re.findall(r'\w+', query.lower())) - stop_words
            is_corrigendum_query = any(w in query.lower() for w in ["corrigendum", "corrigenda", "addendum", "amendment"])

            candidate_items = []
            for doc, meta, distance in zip(documents, metadatas, distances):
                doc_lower = doc.lower()
                clause_lower = str(meta.get("clause_id", "")).lower()
                source_lower = str(meta.get("source_file", "")).lower()
                doc_type_lower = str(meta.get("document_type", "")).lower()

                match_count = sum(1 for term in q_terms if term in doc_lower)
                clause_match = any(term in clause_lower for term in q_terms if len(term) > 2)
                source_match = any(term in source_lower for term in q_terms if len(term) > 2)

                boost = (match_count ** 2) * 15.0 + (10.0 if clause_match else 0.0) + (15.0 if source_match else 0.0)
                if is_corrigendum_query and (doc_type_lower == "corrigendum" or "corrigendum" in source_lower or "addendum" in source_lower):
                    boost += 150.0

                hybrid_score = distance / (1.0 + boost)

                citation = EvidenceCitation(
                    source_file=meta.get("source_file", "unknown"),
                    page_number=meta.get("page_number"),
                    clause_id=meta.get("clause_id"),
                    excerpt=doc[:300] + ("..." if len(doc) > 300 else "")
                )
                snippet_text = doc[:250] + ("..." if len(doc) > 250 else "")

                candidate_items.append({
                    "text": doc,
                    "snippet": snippet_text,
                    "metadata": meta,
                    "distance": distance,
                    "hybrid_score": hybrid_score,
                    "citation": citation
                })

            candidate_items.sort(key=lambda x: x["hybrid_score"])

            # Balanced Context Routing: Ensure dual-context representation (vendor proposal + tender rules) for vendor queries
            is_vendor_query = any(w in query.lower() for w in ["vendor", "bidder", "supplier", "who", "which", "proposal", "advance", "oem", "submitted", "quote", "price"])

            if is_vendor_query:
                vendor_chunks = [item for item in candidate_items if item["metadata"].get("document_type") == "vendor_proposal"]
                tender_chunks = [item for item in candidate_items if item["metadata"].get("document_type") != "vendor_proposal"]

                selected = []
                if vendor_chunks:
                    selected.extend(vendor_chunks[:max(2, n_results // 2)])
                if tender_chunks:
                    selected.extend(tender_chunks[:max(2, n_results // 2)])

                seen_ids = set(id(x) for x in selected)
                for item in candidate_items:
                    if len(selected) >= n_results:
                        break
                    if id(item) not in seen_ids:
                        selected.append(item)
                        seen_ids.add(id(item))

                formatted_results = selected
            else:
                formatted_results = candidate_items[:n_results]

            logger.info(f"Retrieved {len(formatted_results)} chunks with hybrid keyword re-ranking")
            return formatted_results

        except Exception as e:
            logger.exception(f"Retriever error: {e}")
            return []

    def get_indexed_sources(self, tender_id: str) -> List[str]:
        """Returns list of unique source filenames indexed in ChromaDB for tender_id."""
        try:
            collection = self.chroma_manager.get_or_create_collection(tender_id)
            if collection.count() == 0:
                return []
            docs = collection.get()
            metas = docs.get("metadatas", [])
            sources = sorted(list(set(m.get("source_file") for m in metas if m and m.get("source_file"))))
            return sources
        except Exception as e:
            logger.warning(f"Error fetching indexed sources for '{tender_id}': {e}")
            return []

    @traceable(name="RAG Synthesize Answer")
    def synthesize_answer(
        self,
        tender_id: str,
        query: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Synthesizes a direct, concise, evidence-backed answer to a user query using retrieved chunks."""
        # 1. Target Document Absence Verification
        indexed_sources = self.get_indexed_sources(tender_id)
        target_doc_matches = re.findall(
            r'(\b[\w\-\.]+\.(?:pdf|docx|eml|xlsx|txt|csv)\b|\bcorrigendum[_\-\s]*\d+\b|\baddendum[_\-\s]*\d+\b)',
            query,
            re.IGNORECASE
        )

        if target_doc_matches:
            target_raw = target_doc_matches[0]
            target_clean = re.sub(r'[^a-zA-Z0-9]', '', target_raw.lower())

            target_found = any(
                target_clean in re.sub(r'[^a-zA-Z0-9]', '', src.lower())
                for src in indexed_sources
            )

            if not target_found:
                avail_src_str = ", ".join([f"`{s}`" for s in indexed_sources]) if indexed_sources else "None"
                warning_msg = (
                    f" **Target Document Not Indexed:** Document `{target_raw}` is **not currently uploaded or indexed** in tender package `{tender_id}`.\n\n"
                    f" **Currently Indexed Source Files:** {avail_src_str}\n\n"
                    f" **Action Required:** Please upload `{target_raw}` in **Page 1 (Tender Workspace)** and click **'Process & Index'** to include it in RAG search and evaluation."
                )
                logger.warning(f"Target document '{target_raw}' referenced in query '{query}' is not indexed in tender '{tender_id}'.")
                return {
                    "query": query,
                    "synthesized_answer": warning_msg,
                    "results": []
                }

        results = self.search_tender_knowledge(tender_id=tender_id, query=query, n_results=n_results)
        if not results:
            return {
                "query": query,
                "synthesized_answer": f"No relevant clauses found in tender '{tender_id}' matching '{query}'.",
                "results": []
            }

        top_chunk = results[0]
        meta = top_chunk.get("metadata", {})
        source_file = meta.get("source_file", "unknown")
        page_num = meta.get("page_number", 1)
        clause_id = meta.get("clause_id", f"Page {page_num}")

        mistral_api_key = os.getenv("MISTRAL_API_KEY") or os.getenv("LLM_API_KEY")

        if mistral_api_key and mistral_api_key not in ["your_mistral_api_key_here", "your_llm_api_key_here"]:
            try:
                context_str = self.get_context_for_llm(tender_id, query, n_results=n_results)
                prompt = (
                    f"You are a GeM Tender Procurement AI Specialist. Answer the user question directly, accurately, and completely "
                    f"using ONLY the provided tender context. Include all specific technical parameters, values, warranties, or requirements requested.\n\n"
                    f"Question: {query}\n\n"
                    f"Context:\n{context_str}\n\n"
                    f"Instructions: Give a direct answer with all relevant specifications. End with explicit source citation."
                )

                synthesized = None
                try:
                    from mistralai import Mistral
                    m_model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
                    client = Mistral(api_key=mistral_api_key)
                    resp = client.chat.complete(
                        model=m_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    )
                    synthesized = resp.choices[0].message.content.strip()
                except Exception as mistral_sdk_err:
                    logger.debug(f"Mistral SDK call skipped ({mistral_sdk_err}), using REST endpoint...")

                if not synthesized:
                    url = "https://api.mistral.ai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {mistral_api_key}",
                        "Content-Type": "application/json"
                    }
                    body = {
                        "model": os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 350
                    }
                    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=15) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        synthesized = res_data["choices"][0]["message"]["content"].strip()

                if synthesized:
                    return {
                        "query": query,
                        "synthesized_answer": synthesized,
                        "results": results
                    }
            except Exception as llm_err:
                logger.warning(f"Mistral API synthesis call failed ({llm_err}). Using rule-based fact extractor fallback.")

        # Heuristic / Rule-based Fact Extraction Fallback
        merged_texts = []
        seen_texts = set()
        for r in results:
            t = r.get("text", "").strip()
            if t and t not in seen_texts:
                seen_texts.add(t)
                merged_texts.append(t)

        citation_str = f"Source: {source_file}, Page {page_num}, Clause: {clause_id}."
        combined_body = "\n\n".join(merged_texts)
        synthesized = f"{combined_body}\n\n({citation_str})"

        return {
            "query": query,
            "synthesized_answer": synthesized,
            "results": results
        }

    def get_context_for_llm(
        self,
        tender_id: str,
        query: str,
        n_results: int = 5
    ) -> str:
        """Returns formatted context ready for CrewAI agents."""
        results = self.search_tender_knowledge(tender_id=tender_id, query=query, n_results=n_results)
        if not results:
            return "No relevant context found."

        context_parts = []
        for idx, result in enumerate(results, start=1):
            citation = result["citation"]
            context_parts.append(
                f"SOURCE {idx}\n"
                f"File: {citation.source_file}\n"
                f"Page: {citation.page_number}\n"
                f"Clause: {citation.clause_id}\n\n"
                f"Content:\n{result['text']}\n"
            )

        return "\n".join(context_parts)