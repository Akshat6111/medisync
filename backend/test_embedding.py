from app.ai.embeddings import embed_text

embedding = embed_text("Paracetamol is used for fever.")

print(len(embedding))