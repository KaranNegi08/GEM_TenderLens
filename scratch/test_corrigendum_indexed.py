from rag.retriever import KnowledgeRetriever

retriever = KnowledgeRetriever()
res = retriever.synthesize_answer('GEM_8123456', 'Has any finding been affected by a recent corrigendum?')
ans = res['synthesized_answer'].encode('ascii', 'replace').decode('ascii')
print("=== SYNTHESIZED ANSWER FOR CORRIGENDUM QUERY ===")
print(ans)

print("\n=== CITATIONS ===")
for r in res['results']:
    meta = r['metadata']
    src = str(meta.get('source_file')).encode('ascii', 'replace').decode('ascii')
    clause = str(meta.get('clause_id')).encode('ascii', 'replace').decode('ascii')
    print(f"Source: {src} | Page: {meta.get('page_number')} | Clause: {clause}")
