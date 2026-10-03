import re
from typing import Optional
from rapidfuzz import fuzz, process

from app.services.salt_dictionary import (
    SEARCHABLE_NAMES_MAP,
    ALL_SEARCHABLE_KEYS,
    SALT_DICTIONARY,
    _normalize_name,
)
from app.services.drug_dictionary import COMMON_DRUG_NAMES

STOP_WORDS = {
    "what", "is", "are", "the", "used", "for", "tell", "me", "about",
    "can", "you", "explain", "side", "effects", "of", "how", "to", "take",
    "dose", "dosage", "tablet", "syrup", "capsule", "medicine", "drug",
    "should", "i", "a", "an", "in", "with", "does", "have", "please",
    "details", "information", "info", "on", "and", "or", "safe"
}


def clean_drug_query(query: str) -> str:
    """Removes common conversational filler words to isolate the core medicine name."""
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    return " ".join(filtered) if filtered else query.lower().strip()


def lookup_drug_catalog(query: str) -> Optional[str]:
    """
    Checks the verified drug catalogs (salt_dictionary.py and drug_dictionary.py).
    If the queried drug is found, returns structured verified pharmacological reference data.
    If the drug is NOT present (e.g. 'Ozotel 40'), returns None so the LLM falls back
    to general medical knowledge without false name-matching.
    """
    if not query or len(query.strip()) < 2:
        return None

    cleaned = clean_drug_query(query)
    normalized = _normalize_name(cleaned)
    raw_norm = _normalize_name(query)

    # 1. Exact match in SEARCHABLE_NAMES_MAP (brand or active salt)
    for candidate in [normalized, raw_norm, cleaned]:
        if candidate and candidate in SEARCHABLE_NAMES_MAP:
            canonical, salt_key, form, is_brand = SEARCHABLE_NAMES_MAP[candidate]
            entry = SALT_DICTIONARY[salt_key]
            return _format_catalog_entry(canonical, entry, is_brand)

    # 2. Token-level exact match across individual tokens for multi-word queries
    tokens = [t for t in re.split(r"[\s,;]+", cleaned) if len(t) >= 4]
    for token in tokens:
        if token in SEARCHABLE_NAMES_MAP:
            canonical, salt_key, form, is_brand = SEARCHABLE_NAMES_MAP[token]
            entry = SALT_DICTIONARY[salt_key]
            return _format_catalog_entry(canonical, entry, is_brand)

    # 3. High-threshold token_sort_ratio (>= 88) on whole phrase to absorb minor spelling typos (e.g. 'augmntin')
    # but strictly prevent false matches on dissimilar names like 'ozotel 40' -> 'pan 40'
    for candidate in [normalized, raw_norm]:
        if len(candidate) >= 4:
            match = process.extractOne(
                candidate,
                ALL_SEARCHABLE_KEYS,
                scorer=fuzz.token_sort_ratio,
            )
            if match and match[1] >= 88:
                matched_key = match[0]
                canonical, salt_key, form, is_brand = SEARCHABLE_NAMES_MAP[matched_key]
                entry = SALT_DICTIONARY[salt_key]
                return _format_catalog_entry(canonical, entry, is_brand)

    # 4. Check COMMON_DRUG_NAMES from drug_dictionary (standalone generic compounds)
    for drug in COMMON_DRUG_NAMES:
        pattern = r"\b" + re.escape(drug.lower()) + r"\b"
        if re.search(pattern, query.lower()):
            return (
                "=== VERIFIED DRUG CATALOG DATA ===\n"
                f"Matched Compound: {drug}\n"
                f"Generic Name: {drug}\n"
                "Classification: Standard Clinical Pharmaceutical Reference Compound\n"
                f"Status: Verified active pharmacological entity recognized in Indian pharmacopoeia.\n"
            )

    return None


def _format_catalog_entry(matched_name: str, entry: dict, is_brand: bool) -> str:
    generic_name = entry.get("generic_name", matched_name)
    category = entry.get("category", "General Clinical")
    description = entry.get("description", "")
    how_to_use = entry.get("how_to_use", "Take strictly as directed by the prescribing physician.")
    strengths = ", ".join(entry.get("common_strengths", [])) or "Standard clinical strengths"
    side_effects = ", ".join(entry.get("side_effects", [])) or "Consult package insert or physician"
    substitutes = ", ".join(entry.get("brands", [])[:6])

    lines = [
        "=== VERIFIED DRUG CATALOG DATA ===",
        f"Query Matched To: {matched_name} ({'Branded Medication' if is_brand else 'Active Salt'})",
        f"Active Chemical Salt: {generic_name}",
        f"Therapeutic Category: {category}",
        f"Description & Indication: {description}",
        f"Standard Clinical Strengths: {strengths}",
        f"Administration Guidance: {how_to_use}",
        f"Known Common Side Effects: {side_effects}",
    ]
    if substitutes:
        lines.append(f"Verified Bioequivalent Substitutes: {substitutes}")

    return "\n".join(lines)
