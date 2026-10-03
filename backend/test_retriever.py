from app.ai.retriever import retrieve_context

query = "What are the symptoms of diabetes?"

contexts = retrieve_context(query)

print("\nRetrieved Chunks:\n")

for i, context in enumerate(contexts, start=1):
    print(f"------ Chunk {i} ------")
    print(context)
    print()