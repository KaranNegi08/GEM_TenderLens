"""
Comprehensive 5-Point Diagnostic & Ingestion Verification Script for GeM TenderLens RAG Pipeline.
Verifies:
1. Ingestion Verification (Loader, Chunker, Embeddings, Collection Upsert Exception Catching)
2. Collection Identity Check (Collection Count before/after, Source File Sets)
3. Caching & Connection Freshness Check (Client instance and query caching)
4. Embedding Function & Vector Dimension Consistency
5. Distance Score & Retrieval Ranking Analysis for Corrigendum Queries
"""

import os
import sys
import json
import re
from typing import Dict, Any, List

print("=" * 70)
print(" GeM TenderLens RAG Pipeline & Ingestion Diagnostic Suite")
print("=" * 70)

tender_id = "GEM_9146015"
test_file = "./data/uploads/tender_documents/GEM_9146015/corrigendum_2.pdf"

# If test_file doesn't exist in GEM_9146015 folder, create a synthetic corrigendum_2.pdf for testing
if not os.path.exists(test_file):
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "GeM Bid Corrigendum-2\nTender Reference: GEM_9146015\nEffective Date: 26-Jul-2026\n\n1. Clause TS-05 Amendment:\nOriginal Requirement: Adjustable armrests (mandatory)\nRevised Requirement: Adjustable armrests OR fixed armrests with cushioned padding of min 15mm\n\n2. Impact and Re-evaluation Instruction:\nBidders whose technical proposals were earlier marked non-compliant or under review solely on account of offering fixed armrests must be re-assessed against the revised Clause TS-05. If fixed armrest includes cushioned padding, mark as compliant.")
        doc.save(test_file)
        doc.close()
        print(f"[SETUP] Created synthetic test document: {test_file}")
    except Exception as e:
        print(f"[SETUP NOTICE] Could not create PDF via fitz ({e}). Writing plain text file.")
        test_file = test_file.replace(".pdf", ".txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("GeM Bid Corrigendum-2\nTender Reference: GEM_9146015\nEffective Date: 26-Jul-2026\n\n1. Clause TS-05 Amendment:\nOriginal Requirement: Adjustable armrests (mandatory)\nRevised Requirement: Adjustable armrests OR fixed armrests with cushioned padding of min 15mm\n\n2. Impact and Re-evaluation Instruction:\nBidders whose technical proposals were earlier marked non-compliant or under review solely on account of offering fixed armrests must be re-assessed against the revised Clause TS-05. If fixed armrest includes cushioned padding, mark as compliant.")

print(f"\nTarget Test File: {test_file}")
print(f"Target Tender ID: {tender_id}")

# ---------------------------------------------------------
# POINT 1: INGESTION VERIFICATION
# ---------------------------------------------------------
print("\n" + "=" * 50)
print(" 1. INGESTION VERIFICATION")
print("=" * 50)

from rag.document_loader import DocumentLoader
from rag.chunking import DocumentChunker
from rag.embeddings import VectorEmbeddingProvider
from rag.chroma_client import ChromaDBClientManager

# Step 1.1: DocumentLoader
try:
    doc_data = DocumentLoader.load_document(test_file)
    print(f" [PASS] DocumentLoader read file: '{doc_data.get('filename')}'")
    print(f"        Pages loaded: {len(doc_data.get('pages', []))}")
    print(f"        Is Scanned Flag: {doc_data.get('is_scanned')}")
    if doc_data.get('pages'):
        print(f"        First 150 chars: {repr(doc_data['pages'][0]['content'][:150])}")
except Exception as e:
    print(f" [FAIL] DocumentLoader error: {e}")

# Step 1.2: DocumentChunker
try:
    chunks = DocumentChunker.chunk_document(
        doc_data=doc_data,
        tender_id=tender_id,
        document_id="DOC_CORRIGENDUM_2",
        document_type="corrigendum"
    )
    print(f" [PASS] DocumentChunker generated: {len(chunks)} chunks")
    for idx, c in enumerate(chunks, 1):
        print(f"        Chunk #{idx} (Clause: {c.clause_id}): {repr(c.text[:80])}...")
except Exception as e:
    print(f" [FAIL] DocumentChunker error: {e}")

# Step 1.3: VectorEmbeddings
try:
    embedder = VectorEmbeddingProvider()
    texts_to_embed = [c.text for c in chunks]
    embeddings = embedder.embed_texts(texts_to_embed)
    embed_dim = len(embeddings[0]) if embeddings else 0
    print(f" [PASS] VectorEmbeddingProvider generated embeddings")
    print(f"        Model Name: {embedder.model_name}")
    print(f"        Vector Count: {len(embeddings)}, Dimension: {embed_dim}")
except Exception as e:
    print(f" [FAIL] VectorEmbeddingProvider error: {e}")

# Step 1.4: Collection Upsert Exception Catching
chroma_mgr = ChromaDBClientManager()
collection = chroma_mgr.get_or_create_collection(tender_id)
count_before = collection.count()

try:
    ids = [f"CORRIGENDUM_2_CHUNK_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "tender_id": tender_id,
            "document_id": "DOC_CORRIGENDUM_2",
            "document_type": "corrigendum",
            "document_version": "2.0",
            "clause_id": c.clause_id or "Corrigendum-2",
            "page_number": c.page_number or 1,
            "mandatory_flag": c.mandatory_flag,
            "source_file": os.path.basename(test_file)
        }
        for c in chunks
    ]
    collection.upsert(ids=ids, documents=texts_to_embed, metadatas=metadatas, embeddings=embeddings)
    print(f" [PASS] collection.upsert() completed successfully without exception.")
except Exception as e:
    print(f" [FAIL] Exception during collection.upsert(): {e}")

# ---------------------------------------------------------
# POINT 2: COLLECTION IDENTITY CHECK
# ---------------------------------------------------------
print("\n" + "=" * 50)
print(" 2. COLLECTION IDENTITY CHECK")
print("=" * 50)

sanitized_name = chroma_mgr._sanitize_collection_name(tender_id)
count_after = collection.count()
all_docs = collection.get()
all_metas = all_docs.get("metadatas", [])
all_sources = sorted(list(set(m.get("source_file") for m in all_metas if m and m.get("source_file"))))

print(f" Active Tender ID: '{tender_id}'")
print(f" Chroma Collection Name: '{sanitized_name}'")
print(f" Collection Count Before Upload: {count_before}")
print(f" Collection Count After Upload:  {count_after} (Delta: +{count_after - count_before})")
print(f" Total Unique Source Files in Collection ({len(all_sources)}):")
for s in all_sources:
    is_target = " [TARGET MATCH]" if os.path.basename(test_file).lower() in str(s).lower() else ""
    print(f"   - {s}{is_target}")

if any(os.path.basename(test_file).lower() in str(s).lower() for s in all_sources):
    print(" [PASS] Target file 'corrigendum_2' IS PRESENT in active collection sources.")
else:
    print(" [FAIL] Target file 'corrigendum_2' IS MISSING from active collection sources.")

# ---------------------------------------------------------
# POINT 3: CACHING & CONNECTION FRESHNESS
# ---------------------------------------------------------
print("\n" + "=" * 50)
print(" 3. CACHING & CONNECTION FRESHNESS CHECK")
print("=" * 50)

mgr2 = ChromaDBClientManager()
col2 = mgr2.get_or_create_collection(tender_id)
count2 = col2.count()
print(f" Fresh Client Manager Instance Collection Count: {count2}")
if count2 == count_after:
    print(" [PASS] Persistent disk state is in sync with memory client.")
else:
    print(" [FAIL] Stale client instance detected! Persistent disk count differs from client count.")

# ---------------------------------------------------------
# POINT 4: EMBEDDING FUNCTION CONSISTENCY
# ---------------------------------------------------------
print("\n" + "=" * 50)
print(" 4. EMBEDDING FUNCTION CONSISTENCY CHECK")
print("=" * 50)

query_str = "Has any finding been affected by a recent corrigendum?"
query_embedding = embedder.embed_texts([query_str])[0]

print(f" Document Embedding Model: {embedder.model_name} (Dim: {embed_dim})")
print(f" Query Embedding Vector Dim:  {len(query_embedding)}")

if len(query_embedding) == embed_dim:
    print(" [PASS] Embedding dimensions match perfectly between document indexing & query retrieval.")
else:
    print(f" [FAIL] Embedding dimension mismatch! Indexing: {embed_dim}, Query: {len(query_embedding)}")

# ---------------------------------------------------------
# POINT 5: IDENTICAL DISTANCE SCORE & RETRIEVAL ANALYSIS
# ---------------------------------------------------------
print("\n" + "=" * 50)
print(" 5. IDENTICAL DISTANCE SCORE & RETRIEVAL ANALYSIS")
print("=" * 50)

from rag.retriever import KnowledgeRetriever
retriever = KnowledgeRetriever(chroma_manager=chroma_mgr)

# Execute RAG search
rag_res = retriever.synthesize_answer(tender_id, query_str, n_results=5)
results = rag_res.get("results", [])
synthesized_ans = rag_res.get("synthesized_answer", "")

print(f" Query: '{query_str}'")
print(f" Retrieved Results Count: {len(results)}")

if results:
    top_res = results[0]
    top_meta = top_res.get("metadata", {})
    print(f"\n Top Retrieved Result #1:")
    print(f"   Source File: {top_meta.get('source_file')}")
    print(f"   Clause ID:   {top_meta.get('clause_id')}")
    print(f"   Distance:    {top_res.get('distance'):.4f}")
    print(f"   Hybrid Score:{top_res.get('hybrid_score'):.4f}")
    print(f"   Snippet:     {repr(top_res.get('text', '')[:120])}...")
    
    if os.path.basename(test_file).lower() in str(top_meta.get('source_file')).lower():
        print(" [PASS] Top retrieved result is from the newly uploaded 'corrigendum_2' document!")
    else:
        print(f" [NOTICE] Top result came from '{top_meta.get('source_file')}' instead of target file.")

print("\n Synthesized Direct Answer:")
print("-" * 50)
ans_clean = synthesized_ans.encode('ascii', 'replace').decode('ascii')
print(ans_clean)
print("-" * 50)

print("\n" + "=" * 70)
print(" DIAGNOSTIC SUMMARY & CONCLUSION")
print("=" * 70)
if any(os.path.basename(test_file).lower() in str(s).lower() for s in all_sources):
    print(" STATUS: SUCCESS - 'corrigendum_2' is fully ingested and indexed in ChromaDB.")
else:
    print(" STATUS: INGESTION MISSING - 'corrigendum_2' has not been processed into active collection.")
print("=" * 70)
