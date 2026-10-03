import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 1800  # 30 minutes

# Patient ground truth context cache: session_key -> {"patient_context": str, "created_at": float}
_PATIENT_CONTEXT_CACHE: Dict[str, Dict[str, Any]] = {}

# Query-level retrieval cache: query_clean -> {"chunks": List[str], "created_at": float}
_RETRIEVAL_CACHE: Dict[str, Dict[str, Any]] = {}

# Backward compatibility alias
_SESSION_CONTEXT_CACHE = _PATIENT_CONTEXT_CACHE


def get_cached_patient_context(session_key: str) -> Optional[str]:
    entry = _PATIENT_CONTEXT_CACHE.get(session_key)
    if entry and (time.time() - entry["created_at"] < CACHE_TTL_SECONDS):
        return entry.get("patient_context")
    return None


def set_cached_patient_context(session_key: str, patient_context: str):
    _PATIENT_CONTEXT_CACHE[session_key] = {
        "patient_context": patient_context,
        "created_at": time.time(),
    }


def get_cached_retrieval(query: str) -> Optional[List[str]]:
    q = query.strip().lower()
    entry = _RETRIEVAL_CACHE.get(q)
    if entry and (time.time() - entry["created_at"] < CACHE_TTL_SECONDS):
        return entry.get("chunks")
    return None


def set_cached_retrieval(query: str, chunks: List[str]):
    q = query.strip().lower()
    _RETRIEVAL_CACHE[q] = {
        "chunks": chunks,
        "created_at": time.time(),
    }


def clear_session_cache(session_id: Optional[str] = None, user_id: Optional[Any] = None):
    """
    Clears cached session context for a specific session or user.
    """
    global _PATIENT_CONTEXT_CACHE, _RETRIEVAL_CACHE
    if user_id and session_id:
        key = f"{user_id}:{session_id.strip()}"
        _PATIENT_CONTEXT_CACHE.pop(key, None)
    elif user_id:
        prefix = f"{user_id}:"
        keys_to_del = [k for k in _PATIENT_CONTEXT_CACHE if k.startswith(prefix)]
        for k in keys_to_del:
            _PATIENT_CONTEXT_CACHE.pop(k, None)
    elif session_id:
        suffix = f":{session_id.strip()}"
        keys_to_del = [k for k in _PATIENT_CONTEXT_CACHE if k.endswith(suffix)]
        for k in keys_to_del:
            _PATIENT_CONTEXT_CACHE.pop(k, None)
    else:
        _PATIENT_CONTEXT_CACHE.clear()
        _RETRIEVAL_CACHE.clear()
