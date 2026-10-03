import logging
from typing import List

from app.ai.embeddings import embed_text
from app.ai.vectorstore import get_index

logger = logging.getLogger(__name__)


def retrieve_context(query: str, top_k: int = 2) -> List[str]:
    """
    Search Pinecone vectorstore and return the most relevant text chunks.
    Safely catches connection or index errors.
    Bypasses gracefully if the embedding model is still warming up.
    """
    try:
        query_embedding = embed_text(query, timeout=2.0)
        if query_embedding is None:
            logger.info("Embedding model still warming up; safely bypassing vectorstore retrieval for instant response.")
            return []

        index = get_index()
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )

        contexts = []
        for match in results.matches:
            if match.metadata and "text" in match.metadata:
                contexts.append(match.metadata["text"])

        return contexts
    except Exception as e:
        logger.warning(f"Vectorstore retrieval bypassed or failed: {e}")
        return []