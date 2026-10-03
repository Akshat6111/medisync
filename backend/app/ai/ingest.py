import time
import uuid

from app.ai.loader import load_documents, split_documents
from app.ai.embeddings import embed_texts
from app.ai.vectorstore import get_index


BATCH_SIZE = 25


def ingest():
    print("Loading PDFs...")
    documents = load_documents()

    print(f"Loaded {len(documents)} document(s)")

    chunks = split_documents(documents)

    total_chunks = len(chunks)

    print(f"Created {total_chunks} chunks")

    index = get_index()

    print("Starting upload...\n")

    uploaded = 0

    for i in range(0, total_chunks, BATCH_SIZE):

        batch_chunks = chunks[i:i + BATCH_SIZE]

        texts = [chunk.page_content for chunk in batch_chunks]

        embeddings = embed_texts(texts)

        vectors = []

        for chunk, embedding in zip(batch_chunks, embeddings):
            vectors.append(
                {
                    "id": str(uuid.uuid4()),
                    "values": embedding,
                    "metadata": {
                        "text": chunk.page_content,
                        "source": chunk.metadata.get("source", ""),
                        "page": chunk.metadata.get("page", -1),
                    },
                }
            )

        while True:
            try:
                index.upsert(vectors=vectors)

                uploaded += len(vectors)

                print(f"Uploaded {uploaded}/{total_chunks}")

                break

            except Exception as e:

                print("\nConnection lost!")
                print(e)

                print("Retrying in 5 seconds...\n")

                time.sleep(5)

    print("\n✅ Ingestion completed successfully!")