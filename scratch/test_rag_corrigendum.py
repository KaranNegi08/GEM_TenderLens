from rag.retriever import KnowledgeRetriever

retriever = KnowledgeRetriever()

# Test 1: Query referencing un-indexed document corrigendum_2.pdf
res1 = retriever.synthesize_answer("GEM_9146015", "Does corrigendum_2.pdf affect any finding?")
print("=== TEST 1 (Un-indexed document query) ===")
ans1 = res1["synthesized_answer"].encode('ascii', 'replace').decode('ascii')
print("Answer:\n", ans1)
print("Results count:", len(res1["results"]))

# Test 2: Query referencing indexed document technical_spec.pdf
res2 = retriever.synthesize_answer("GEM_9146015", "What are the laptop specs in technical_spec.pdf?")
print("\n=== TEST 2 (Indexed document query) ===")
ans2 = res2["synthesized_answer"].encode('ascii', 'replace').decode('ascii')
print("Answer snippet:\n", ans2[:250])
print("Results count:", len(res2["results"]))
