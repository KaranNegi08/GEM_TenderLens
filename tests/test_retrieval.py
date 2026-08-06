"""
Unit tests for ChromaDB retrieval and client manager.
"""

from rag.chroma_client import ChromaDBClientManager
from rag.retriever import KnowledgeRetriever

import tempfile

def test_chroma_client_manager(tmp_path=None):
    dir_path = str(tmp_path) if tmp_path else tempfile.mkdtemp()
    manager = ChromaDBClientManager(persist_directory=dir_path)
    col = manager.get_or_create_collection("GEM/2026/B/7798305")
    assert col is not None
    assert "tender_gem_2026_b_7798305" in manager.list_collections()[0]

def test_knowledge_retriever(tmp_path=None):
    dir_path = str(tmp_path) if tmp_path else tempfile.mkdtemp()
    manager = ChromaDBClientManager(persist_directory=dir_path)
    retriever = KnowledgeRetriever(chroma_manager=manager)
    col = manager.get_or_create_collection("GEM_TEST_123")
    
    docs = ["Mandatory delivery limit: 21 days."]
    embeds = retriever.embedding_provider.embed_texts(docs)

    col.add(
        ids=["chunk_1"],
        documents=docs,
        embeddings=embeds,
        metadatas=[{"source_file": "bid.pdf", "page_number": 1, "mandatory_flag": True}]
    )
    
    results = retriever.search_tender_knowledge("GEM_TEST_123", "delivery limit")
    assert len(results) == 1
    assert "21 days" in results[0]["text"]

def test_synthesize_answer(tmp_path=None):
    dir_path = str(tmp_path) if tmp_path else tempfile.mkdtemp()
    manager = ChromaDBClientManager(persist_directory=dir_path)
    retriever = KnowledgeRetriever(chroma_manager=manager)
    col = manager.get_or_create_collection("GEM_TEST_456")
    
    docs = ["EMD Amount: Rs. 50,000/- (MSE/Startup registered on GeM are exempted from EMD)."]
    embeds = retriever.embedding_provider.embed_texts(docs)

    col.add(
        ids=["chunk_1"],
        documents=docs,
        embeddings=embeds,
        metadatas=[{"source_file": "tender_document.pdf", "page_number": 1, "clause_id": "Clause 1.2", "mandatory_flag": True}]
    )
    
    synthesis = retriever.synthesize_answer("GEM_TEST_456", "What is the EMD amount?")
    assert synthesis["synthesized_answer"] != ""
    assert "50,000" in synthesis["synthesized_answer"] or "EMD" in synthesis["synthesized_answer"]
    assert len(synthesis["results"]) == 1



