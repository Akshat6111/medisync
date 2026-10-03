import logging
import os
import threading
from typing import List, Optional

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()
_warmup_event = threading.Event()
_is_warming_up = False


def is_model_ready() -> bool:
    """Returns True if the embedding model is loaded in memory and ready."""
    return _model is not None


def get_embedding_model(timeout: Optional[float] = None):
    """
    Thread-safe retrieval of the SentenceTransformer model.
    Loads from local cache first to avoid remote HuggingFace network delays.
    If timeout is specified and warmup is still running, waits up to timeout seconds.
    """
    global _model, _is_warming_up
    if _model is not None:
        return _model

    # If timeout is specified and background warmup is actively running, wait on the event
    if timeout is not None and not is_model_ready():
        if _is_warming_up:
            _warmup_event.wait(timeout=timeout)
            if _model is not None:
                return _model
            return None

    with _model_lock:
        if _model is not None:
            return _model

        try:
            # Optimize HuggingFace environment flags
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
            os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
            from sentence_transformers import SentenceTransformer

            try:
                # 1. First attempt: load strictly from local cache (fastest, 0 network overhead)
                _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            except Exception:
                # 2. Fallback: if not locally cached, allow online download
                _model = SentenceTransformer("all-MiniLM-L6-v2")

            _warmup_event.set()
            return _model
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            _warmup_event.set()
            return None


def warmup_embeddings():
    """Synchronous warmup of the embedding model."""
    global _is_warming_up
    if is_model_ready():
        return
    _is_warming_up = True
    try:
        logger.info("Pre-warming SentenceTransformer embedding model in background...")
        model = get_embedding_model(timeout=None)
        if model:
            # Dummy encode to prime PyTorch weights & memory
            model.encode("warmup")
            logger.info("SentenceTransformer embedding model is pre-warmed and ready!")
    except Exception as e:
        logger.warning(f"Embedding model warmup warning: {e}")
    finally:
        _is_warming_up = False
        _warmup_event.set()


def warmup_embeddings_async():
    """Asynchronous background warmup to avoid blocking server boot."""
    if is_model_ready():
        return
    t = threading.Thread(target=warmup_embeddings, daemon=True, name="embedding-warmup")
    t.start()


def embed_text(text: str, timeout: Optional[float] = 2.0) -> Optional[List[float]]:
    """
    Encodes text into vector embeddings.
    Bounded by timeout to prevent freezing the user during chat if model is still loading.
    """
    model = get_embedding_model(timeout=timeout)
    if model is None:
        return None
    return model.encode(text).tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch encodes texts for ingestion."""
    model = get_embedding_model(timeout=None)
    if model is None:
        raise RuntimeError("Embedding model is not available.")
    return model.encode(texts).tolist()