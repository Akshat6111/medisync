"""
Pipeline to fetch, parse, and ingest real drug interactions from openFDA drug labels.

Provenance:
- Drug catalogue sourced from: app.services.drug_dictionary (COMMON_DRUG_NAMES)
- Interaction text sourced from: https://api.fda.gov/drug/label.json
- Stored in: drug_interactions table (source="openfda")
"""

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from rapidfuzz import fuzz, process

from app.db.database import SessionLocal
from app.models.drug_interaction import DrugInteraction
from app.services.drug_dictionary import COMMON_DRUG_NAMES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# PROJECT GAP-HOUR HEURISTIC TABLE
# ============================================================================
# NOTE: OpenFDA drug labeling endpoints provide free-text drug interaction
# sections, clinical warnings, and occasional qualitative severity descriptors,
# but do NOT provide structured quantitative dosing intervals (gap hours).
#
# Therefore, the following minimum_gap_hours mappings are a project-defined
# clinical heuristic designed for the CSP constraint satisfaction scheduler:
#   - severe: 6.0 hours (contraindicated, serious, or high-risk interactions)
#   - moderate: 4.0 hours (standard interaction default requiring spacing)
#   - mild: 2.0 hours (minor interactions where short spacing suffices)
#
# Only interaction existence and qualitative text provenance originate directly
# from openFDA. Gap-hour numerical values are project heuristics for scheduling.
# ============================================================================
SEVERITY_GAP_HOURS: Dict[str, float] = {
    "severe": 6.0,
    "moderate": 4.0,
    "mild": 2.0,
}

SEVERE_KEYWORDS = re.compile(
    r"\b(contraindicated|contraindication|life-threatening|fatal|severe|serious|avoid concomitant|avoid co-administration|do not use|major)\b",
    re.IGNORECASE,
)
MILD_KEYWORDS = re.compile(
    r"\b(minor|mild|slight|minimal)\b",
    re.IGNORECASE,
)

# Common stopwords to avoid spurious fuzzy matches in medical text
COMMON_STOPWORDS = {
    "about", "after", "again", "against", "almost", "along", "already", "also",
    "although", "always", "among", "another", "because", "before", "between",
    "clinical", "concentration", "concentrations", "concomitant", "concomitantly",
    "decrease", "decreased", "decreases", "dosage", "during", "effect", "effects",
    "hepatic", "increase", "increased", "increases", "inhibit", "inhibits",
    "inhibitor", "inhibitors", "inducer", "inducers", "interaction", "interactions",
    "metabolism", "moderate", "monitoring", "patient", "patients", "plasma",
    "potential", "reduced", "reduction", "response", "severe", "serum",
    "should", "studies", "therapy", "treatment", "without",
}


def query_openfda_label(drug_name: str) -> Optional[Tuple[List[str], str]]:
    """
    Queries openFDA /drug/label.json for a drug's drug_interactions section.
    Tries generic_name first, then brand_name.
    Returns (list_of_interaction_texts, source_query_url) or None.
    """
    clean_name = drug_name.strip()
    encoded_name = urllib.parse.quote(f'"{clean_name}"')

    # 1. Search by generic_name
    url_generic = (
        f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{encoded_name}"
        f"+AND+_exists_:drug_interactions&limit=1"
    )

    for attempt in range(2):
        try:
            req = urllib.request.Request(
                url_generic,
                headers={"User-Agent": "MediSync-CSP/1.0 (HealthTech Research)"},
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("results", [])
                if results and results[0].get("drug_interactions"):
                    return results[0]["drug_interactions"], url_generic
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # No match on generic_name, try brand_name
                break
            elif e.code == 429:
                time.sleep(3.0)
                continue
            else:
                logger.debug("HTTP %s for generic %s", e.code, clean_name)
                break
        except Exception as ex:
            logger.debug("Generic query error for %s: %s", clean_name, ex)
            time.sleep(1.0)

    # 2. Fallback search by brand_name
    url_brand = (
        f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{encoded_name}"
        f"+AND+_exists_:drug_interactions&limit=1"
    )

    try:
        req = urllib.request.Request(
            url_brand,
            headers={"User-Agent": "MediSync-CSP/1.0 (HealthTech Research)"},
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("results", [])
            if results and results[0].get("drug_interactions"):
                return results[0]["drug_interactions"], url_brand
    except urllib.error.HTTPError as e:
        if e.code != 404:
            logger.debug("HTTP %s for brand %s", e.code, clean_name)
    except Exception as ex:
        logger.debug("Brand query error for %s: %s", clean_name, ex)

    return None


def resolve_severity(context_snippet: str) -> Tuple[str, bool]:
    """
    Checks if explicit severity keywords exist in the interaction text snippet.
    Returns (severity_level, was_explicitly_detected).
    If no explicit keyword is found, defaults to 'moderate' and flags detected=False.
    """
    if SEVERE_KEYWORDS.search(context_snippet):
        return "severe", True
    if MILD_KEYWORDS.search(context_snippet):
        return "mild", True
    return "moderate", False


def run_pipeline():
    logger.info("Starting openFDA drug interactions ingestion pipeline...")

    # Normalize catalog from COMMON_DRUG_NAMES
    raw_catalog = sorted(list({d.strip() for d in COMMON_DRUG_NAMES if len(d.strip()) >= 3}))
    catalog_lookup = {d.lower(): d for d in raw_catalog}
    catalog_lower_list = list(catalog_lookup.keys())

    logger.info("Total unique drugs in catalog: %d", len(raw_catalog))

    # Metrics
    total_drugs_queried = 0
    total_labels_found = 0
    total_raw_mentions = 0
    total_confident_matches = 0
    total_dropped_low_confidence = 0
    explicit_severity_count = 0
    default_moderate_count = 0

    # Deduplication map: canonical key (drug_min, drug_max) -> row dict
    interaction_pairs: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for idx, drug_name in enumerate(raw_catalog, 1):
        total_drugs_queried += 1
        d_lower = drug_name.lower()

        # Slight pause to stay within openFDA rate limit (~240 req/min)
        time.sleep(0.25)

        res = query_openfda_label(drug_name)
        if not res:
            continue

        interaction_texts, query_url = res
        total_labels_found += 1
        full_text = " ".join(interaction_texts)

        if idx % 25 == 0 or idx == len(raw_catalog):
            logger.info(
                "Progress: %d/%d drugs queried | %d labels found | %d unique pairs",
                idx,
                len(raw_catalog),
                total_labels_found,
                len(interaction_pairs),
            )

        # 1. Exact catalog match check across the label text
        matched_other_drugs: Dict[str, Tuple[str, str]] = {}  # target_lower -> (context_snippet, match_type)

        for target_lower in catalog_lower_list:
            if target_lower == d_lower:
                continue

            # Word boundary regex for exact mention
            pattern = rf"\b{re.escape(target_lower)}\b"
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                total_raw_mentions += 1
                # Extract surrounding window (+/- 150 chars) for snippet & severity
                start = max(0, m.start() - 150)
                end = min(len(full_text), m.end() + 150)
                snippet = full_text[start:end].strip()
                matched_other_drugs[target_lower] = (snippet, "exact")

        # 2. Fuzzy matching on words/tokens in text to catch informal mentions
        # Extract alphanumeric word tokens >= 5 chars
        tokens = set(re.findall(r"\b[a-zA-Z]{5,}\b", full_text))
        for token in tokens:
            token_lower = token.lower()
            if token_lower in COMMON_STOPWORDS or token_lower in matched_other_drugs or token_lower == d_lower:
                continue

            # Fuzzy match against catalog
            best = process.extractOne(
                token_lower,
                catalog_lower_list,
                scorer=fuzz.ratio,
            )
            if best:
                matched_name, score, _ = best
                if matched_name == d_lower:
                    continue

                if score >= 85.0:
                    # Confident fuzzy match
                    total_raw_mentions += 1
                    pos = full_text.lower().find(token_lower)
                    start = max(0, pos - 150) if pos != -1 else 0
                    end = min(len(full_text), pos + 150) if pos != -1 else len(full_text)
                    snippet = full_text[start:end].strip()
                    matched_other_drugs[matched_name] = (snippet, f"fuzzy_{score:.1f}")
                elif 70.0 <= score < 85.0:
                    total_dropped_low_confidence += 1

        # Process matched pairs for this drug label
        for other_lower, (snippet, match_type) in matched_other_drugs.items():
            total_confident_matches += 1

            # Canonical order for deduplication
            drug_a = min(d_lower, other_lower)
            drug_b = max(d_lower, other_lower)
            pair_key = (drug_a, drug_b)

            severity, was_explicit = resolve_severity(snippet)
            if was_explicit:
                explicit_severity_count += 1
            else:
                default_moderate_count += 1

            gap_hours = SEVERITY_GAP_HOURS[severity]

            # Clean snippet for description
            clean_snippet = re.sub(r"\s+", " ", snippet)[:350]
            desc = (
                f"Interaction documented in openFDA label ({clean_name_pair(drug_a, drug_b)}). "
                f"Excerpt: {clean_snippet}"
            )

            # If pair already seen, upgrade severity if new one is more severe
            if pair_key in interaction_pairs:
                existing = interaction_pairs[pair_key]
                if severity == "severe" and existing["severity"] != "severe":
                    existing["severity"] = "severe"
                    existing["minimum_gap_hours"] = SEVERITY_GAP_HOURS["severe"]
                    existing["description"] = desc
                    existing["source_url"] = query_url
            else:
                interaction_pairs[pair_key] = {
                    "id": uuid.uuid4(),
                    "drug_a": drug_a,
                    "drug_b": drug_b,
                    "severity": severity,
                    "minimum_gap_hours": gap_hours,
                    "description": desc,
                    "source": "openfda",
                    "source_url": query_url,
                }

    # Store into Database
    db = SessionLocal()
    try:
        # Clear existing rows (keep table schema)
        cleared_count = db.query(DrugInteraction).delete()
        db.commit()
        logger.info("Cleared %d previous rows from drug_interactions table.", cleared_count)

        # Bulk insert new real openFDA rows
        objects = [DrugInteraction(**row) for row in interaction_pairs.values()]
        db.bulk_save_objects(objects)
        db.commit()
        logger.info("Inserted %d unique openFDA drug interaction rows into DB.", len(objects))
    finally:
        db.close()

    # Calculate final statistics
    total_pairs = len(interaction_pairs)
    total_severity_evaluations = explicit_severity_count + default_moderate_count
    explicit_pct = (
        (explicit_severity_count / total_severity_evaluations * 100)
        if total_severity_evaluations > 0
        else 0.0
    )
    default_pct = (
        (default_moderate_count / total_severity_evaluations * 100)
        if total_severity_evaluations > 0
        else 0.0
    )

    print("\n" + "=" * 70)
    print("OPENFDA REAL DRUG INTERACTION PIPELINE REPORT")
    print("=" * 70)
    print(f"Total drugs in catalog queried:              {total_drugs_queried}")
    print(f"Total drug labels with interactions found:   {total_labels_found}")
    print(f"Total raw drug mentions extracted:           {total_raw_mentions}")
    print(f"Total confident matches (score >= 85):       {total_confident_matches}")
    print(f"Total dropped due to low confidence (70-84): {total_dropped_low_confidence}")
    print(f"Total unique deduplicated pairs stored:      {total_pairs}")
    print("-" * 70)
    print("SEVERITY CLASSIFICATION HONEST ACCOUNTING:")
    print(f"  - Explicitly detected from text:           {explicit_severity_count} ({explicit_pct:.1f}%)")
    print(f"  - Defaulted to 'moderate' (project fallback): {default_moderate_count} ({default_pct:.1f}%)")
    print("=" * 70 + "\n")

    return {
        "total_drugs_queried": total_drugs_queried,
        "total_labels_found": total_labels_found,
        "total_raw_mentions": total_raw_mentions,
        "total_confident_matches": total_confident_matches,
        "total_dropped_low_confidence": total_dropped_low_confidence,
        "total_pairs_stored": total_pairs,
        "explicit_severity_count": explicit_severity_count,
        "explicit_pct": explicit_pct,
        "default_moderate_count": default_moderate_count,
        "default_pct": default_pct,
    }


def clean_name_pair(a: str, b: str) -> str:
    return f"{a.title()} + {b.title()}"


if __name__ == "__main__":
    run_pipeline()
