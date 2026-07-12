"""
app/scripts/seed_interaction.py

Replaces manual curation (CURATED_INTERACTIONS) with real FDA-sourced data,
pulled from openFDA and normalized via RxNorm. No hand-typed medical rules.

Usage:
    python -m app.scripts.seed_interaction

Env (optional but recommended):
    OPENFDA_API_KEY   -> https://open.fda.gov/apis/authentication/

IMPORTANT — one-time migration needed first:
    Your DrugInteraction.minimum_gap_hours column is currently NOT NULL,
    left over from the dropped CSP scheduler. FDA label text has no numeric
    hour-gap value, and we won't fabricate one. Before running this script,
    make the column nullable:

        ALTER TABLE drug_interactions ALTER COLUMN minimum_gap_hours DROP NOT NULL;

    (or the equivalent Alembic migration).
"""

import os
import re
import time
import logging
from typing import Optional

import requests

from app.db.database import SessionLocal
from app.models.drug_interaction import DrugInteraction

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("seed_interaction")

OPENFDA_API_KEY = os.environ.get("OPENFDA_API_KEY")
OPENFDA_BASE = "https://api.fda.gov/drug/label.json"
RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"
REQUEST_DELAY_SECONDS = 0.3

# Expand freely — this is just which drugs to pull labels for, not medical rules.
SEED_DRUGS = [
    "acetaminophen", "ibuprofen", "aspirin", "warfarin", "metformin",
    "atorvastatin", "amlodipine", "lisinopril", "omeprazole", "levothyroxine",
    "amoxicillin", "azithromycin", "metoprolol", "losartan", "gabapentin",
    "sertraline", "fluoxetine", "citalopram", "escitalopram", "simvastatin",
    "hydrochlorothiazide", "furosemide", "prednisone", "insulin", "clopidogrel",
    "tramadol", "diazepam", "alprazolam", "clonazepam", "zolpidem",
    "montelukast", "albuterol", "ciprofloxacin", "doxycycline", "cephalexin",
    "metronidazole", "trimethoprim", "sulfamethoxazole", "digoxin", "heparin",
]

SEVERITY_KEYWORDS = {
    "severe": ["contraindicated", "life-threatening", "fatal", "severe", "should not be used with"],
    "moderate": ["increase the risk", "caution", "monitor", "may increase", "reduced effect"],
    "mild": ["minor", "slight", "may be observed"],
}


def normalize_drug_name(name: str) -> str:
    """Resolve a raw name to its RxNorm preferred ingredient name."""
    try:
        resp = requests.get(f"{RXNAV_BASE}/rxcui.json", params={"name": name, "search": 1}, timeout=10)
        resp.raise_for_status()
        ids = resp.json().get("idGroup", {}).get("rxnormId")
        if not ids:
            return name.strip().lower()

        rxcui = ids[0]
        prop_resp = requests.get(
            f"{RXNAV_BASE}/rxcui/{rxcui}/property.json",
            params={"propName": "RxNorm Name"},
            timeout=10,
        )
        prop_resp.raise_for_status()
        props = prop_resp.json().get("propConceptGroup", {}).get("propConcept", [])
        if props:
            return props[0]["propValue"].strip().lower()
    except (requests.RequestException, KeyError, IndexError) as e:
        log.warning("RxNorm lookup failed for %r: %s", name, e)

    return name.strip().lower()


def fetch_label(generic_name: str) -> Optional[dict]:
    params = {"search": f'openfda.generic_name:"{generic_name}"', "limit": 1}
    if OPENFDA_API_KEY:
        params["api_key"] = OPENFDA_API_KEY

    try:
        resp = requests.get(OPENFDA_BASE, params=params, timeout=15)
        if resp.status_code == 404:
            log.info("No label found for %s", generic_name)
            return None
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None
    except requests.RequestException as e:
        log.warning("openFDA fetch failed for %r: %s", generic_name, e)
        return None


def guess_severity(text: str) -> str:
    text_lower = text.lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return severity
    return "unspecified"


def extract_pairs_from_label(label: dict, this_drug: str, known_drugs: list[str]) -> list[dict]:
    pairs = []
    interaction_text = " ".join(label.get("drug_interactions", []) or [])
    boxed_text = " ".join(label.get("boxed_warning", []) or [])
    full_text = f"{interaction_text} {boxed_text}".strip()

    if not full_text:
        return pairs

    text_lower = full_text.lower()
    spl_set_id = label.get("openfda", {}).get("spl_set_id", [None])[0]
    source_url = (
        f"https://api.fda.gov/drug/label.json?search=openfda.spl_set_id:%22{spl_set_id}%22"
        if spl_set_id else OPENFDA_BASE
    )

    for other_drug in known_drugs:
        if other_drug == this_drug:
            continue
        if re.search(rf"\b{re.escape(other_drug)}\b", text_lower):
            idx = text_lower.find(other_drug)
            snippet = full_text[max(0, idx - 100): idx + 200].strip()

            drug_a, drug_b = sorted([this_drug, other_drug])
            pairs.append({
                "drug_a": drug_a,
                "drug_b": drug_b,
                "severity": guess_severity(snippet),
                # Legacy field from the dropped CSP scheduler. FDA label text
                # doesn't give a numeric hour gap, and we're not going to
                # fabricate one -- left as None (requires the column to be
                # nullable; see migration note in the script docstring).
                "minimum_gap_hours": None,
                "description": snippet[:2000],
                "source": "FDA Drug Label (via openFDA)",
                "source_url": source_url,
            })

    return pairs


def fetch_curated_interactions() -> list[dict]:
    """
    Replacement for the old CURATED_INTERACTIONS constant.
    Builds the same shape of dict list, but sourced from real FDA labels
    instead of hand-typed rules.
    """
    log.info("Normalizing %d seed drug names via RxNorm...", len(SEED_DRUGS))
    normalized = {d: normalize_drug_name(d) for d in SEED_DRUGS}
    known_drugs = list(set(normalized.values()))

    all_pairs = []
    seen = set()

    for raw_name, norm_name in normalized.items():
        log.info("Fetching FDA label for: %s", raw_name)
        label = fetch_label(raw_name)
        time.sleep(REQUEST_DELAY_SECONDS)

        if not label:
            continue

        for pair in extract_pairs_from_label(label, norm_name, known_drugs):
            key = (pair["drug_a"], pair["drug_b"])
            if key in seen:
                continue
            seen.add(key)
            all_pairs.append(pair)

        log.info("  -> %d total unique pairs so far", len(all_pairs))

    return all_pairs


def seed():
    db = SessionLocal()

    try:
        created = 0
        interactions = fetch_curated_interactions()

        for interaction in interactions:
            exists = (
                db.query(DrugInteraction)
                .filter(
                    DrugInteraction.drug_a == interaction["drug_a"],
                    DrugInteraction.drug_b == interaction["drug_b"],
                )
                .first()
            )

            if exists:
                continue

            db.add(DrugInteraction(**interaction))
            created += 1

        db.commit()

        print(f"Seeded {created} interactions successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()