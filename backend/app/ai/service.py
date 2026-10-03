import logging
import re
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.ai.drug_lookup import lookup_drug_catalog
from app.ai.llm import generate_answer
from app.ai.patient_context import get_patient_context
from app.ai.retriever import retrieve_context
from app.models.user import User
from app.ai.cache import (
    _SESSION_CONTEXT_CACHE,
    CACHE_TTL_SECONDS,
    get_cached_patient_context,
    set_cached_patient_context,
    get_cached_retrieval,
    set_cached_retrieval,
    clear_session_cache,
)

logger = logging.getLogger(__name__)

GREETING_PHRASES = [
    "hi", "hello", "hey", "hola", "namaste", "greetings",
    "good morning", "good afternoon", "good evening", "good night",
    "who are you", "what are you", "what can you do", "how can you help",
    "how are you", "what is your name", "help", "thanks", "thank you", "bye"
]

MEDICAL_INDICATORS = [
    "mg", "tablet", "capsule", "syrup", "dose", "dosage", "side effect",
    "interaction", "disease", "condition", "symptom", "pain", "fever",
    "prescribe", "prescription", "use for", "used for", "cure", "treat",
    "indication", "contraindication", "antibiotic", "mechanism"
]

PERSONAL_PATTERNS = [
    r"my\s+(medication|medicine|pill|prescription|dose|schedule|routine|allergy|allergies|condition|profile|record)",
    r"what\s+(medication|medicine|pill|drug)s?(\s+\w+)*\s+(am\s+i|do\s+i|have\s+i)",
    r"(am\s+i|have\s+i|did\s+i)\s+(taking|take|taken)",
    r"(what|when)\s+(should|do)\s+i\s+take",
    r"scheduled\s+(today|for\s+me|now)",
    r"do\s+i\s+have\s+any\s+(medication|medicine|pill|scheduled)",
    r"miss\s+a\s+scheduled\s+dose",
]


def should_skip_medical_retrieval(query: str) -> bool:
    """
    Detects if the query is a greeting, pleasantry, or personal health regimen question
    that relies exclusively on the patient DB record and does not need vectorstore literature search.
    """
    q = query.strip().lower()
    cleaned = re.sub(r"[^\w\s]", "", q).strip()

    # 1. Greetings & conversational pleasantries without clinical drug queries
    is_greeting = any(g in cleaned for g in GREETING_PHRASES)
    has_medical = any(m in q for m in MEDICAL_INDICATORS)
    if is_greeting and not has_medical:
        return True

    # 2. Pure personal-data queries that rely strictly on patient DB record
    if any(re.search(pat, q) for pat in PERSONAL_PATTERNS):
        if not any(k in q for k in ["mechanism of", "literature on", "clinical trial", "pharmacology of"]):
            return True

    return False


def chat(
    query: str,
    db: Session,
    current_user: User,
    history: Optional[List[Dict[str, str]]] = None,
    session_id: Optional[str] = None,
) -> str:
    """
    Coordinates multi-turn AI chat by assembling:
    1. Patient Record Ground Truth (cached per session)
    2. Verified Drug Catalog Data (salt_dictionary / drug_dictionary)
    3. Retrieved Medical Literature Chunks (Pinecone vectorstore, skipped for greetings/personal queries)
    4. Ongoing Conversation History (capped to last 6 messages hard limit)
    """
    cache_key = f"{current_user.id}:{session_id.strip() if session_id else 'default'}"

    # 1. Fetch strict personal patient context (cached per session)
    patient_context = get_cached_patient_context(cache_key)
    if not patient_context:
        patient_context = get_patient_context(db, current_user)
        set_cached_patient_context(cache_key, patient_context)

    # 2. Check verified drug reference catalogs for the specific query
    drug_catalog_context = lookup_drug_catalog(query)

    # 3. Retrieve medical knowledge from vectorstore (Pinecone) only when relevant
    medical_context = None
    if not should_skip_medical_retrieval(query):
        cached_chunks = get_cached_retrieval(query)
        if cached_chunks is not None:
            medical_chunks = cached_chunks
        else:
            medical_chunks = retrieve_context(query)
            set_cached_retrieval(query, medical_chunks)
        medical_context = "\n\n".join(medical_chunks) if medical_chunks else None

    # 4. Enforce strict history cap (last 6 messages hard limit)
    capped_history = history[-6:] if history else []

    # 5. Generate response via LLM
    return generate_answer(
        patient_context=patient_context,
        drug_catalog_context=drug_catalog_context,
        medical_context=medical_context,
        question=query,
        history=capped_history,
    )