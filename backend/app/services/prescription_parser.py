import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from rapidfuzz import fuzz, process

from app.schemas.prescription import (
    ParsedMedicationCandidate,
    PrescriptionParseResponse,
)
from app.services.drug_dictionary import COMMON_DRUG_NAMES
from app.services.prescription_abbreviations import (
    LATIN_FREQUENCY_MAP,
    MEAL_MODIFIER_MAP,
    NUMERIC_SHORTHAND_MAP,
)
from app.services.lab_report_parser import extract_text_from_pdf_or_image

logger = logging.getLogger(__name__)

# Prefixes to strip when isolating drug names
PREFIX_RE = re.compile(
    r"^(?:\d+[\.\)]\s*)?(?:tab(?:let)?\.?|cap(?:sule)?\.?|inj(?:ection)?\.?|syp|syrup\.?|oint(?:ment)?\.?|drop(?:s)?\.?|rx\.?)\s+",
    re.IGNORECASE,
)

# Dosage amount and unit: e.g. 500mg, 500 mg, 0.5 mg, 10ml, 1 tab
DOSAGE_RE = re.compile(
    r"(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|ml|iu|tablets?|capsules?|drops?|puffs?|units?)\b",
    re.IGNORECASE,
)

# Duration in days/weeks: e.g. x 5 days, for 2 weeks, 10d
DURATION_RE = re.compile(
    r"(?:x\s*|for\s*)?(?P<num>\d+)\s*(?P<unit>days?|weeks?|months?|d)\b",
    re.IGNORECASE,
)


def _clean_line_candidate(line: str) -> str:
    """Strip leading numbers, bullets, and doctor prefixes."""
    cleaned = line.strip()
    cleaned = re.sub(r"^[\*\-\•\d+\.\)]+\s*", "", cleaned)
    cleaned = PREFIX_RE.sub("", cleaned)
    return cleaned.strip()


def parse_line_for_medication(
    raw_line: str,
) -> Optional[ParsedMedicationCandidate]:
    """
    Parses an individual line of prescription text into a structured medication candidate.
    Supports single-line notations, tabular rows, compound formulations, and Indian brand names.
    """
    line = re.sub(
        r"\b(Tablet|Capsule|Injection|Syrup|Tab|Cap|Inj)(?=[A-Za-z])",
        r"\1 ",
        raw_line,
        flags=re.IGNORECASE,
    ).strip()
    # Normalize uppercase single/double letter suffixes (e.g. SwitchCV -> Switch CV, EbastM -> Ebast M)
    line = re.sub(r"([a-z])([A-Z]{1,2})\b", r"\1 \2", line)
    if len(line) < 3:
        return None

    lower_line = line.lower()

    # Skip common header / metadata lines UNLESS a dosage form or medical frequency is present
    if any(
        hdr in lower_line
        for hdr in [
            "doctor", "clinic", "hospital", "patient", "reg no", "reg. no",
            "age/sex", "gender:", "address", "signature", "qualification",
            "diagnosis", "bp:", "weight:", "allergies", "investigation",
            "appointment", "housing board", "closed", "dr."
        ]
    ) and not any(
        kw in lower_line
        for kw in [
            "tablet", "capsule", "injection", "tab.", "cap.", "inj.",
            "1-0-1", "1 - 0 - 1", "1-0-0", "0-0-1", "1/2", " 40 mg", " 500 mg", " 325 mg", " 600mg"
        ]
    ):
        return None

    # 1. Route detection
    route = "oral"
    if any(kw in lower_line for kw in ["injection", "inj", "intramuscular", "im ", "iv "]):
        route = "injection"
    elif any(kw in lower_line for kw in ["ointment", "cream", "gel"]):
        route = "topical"
    elif "drop" in lower_line:
        route = "drops"
    elif "syp" in lower_line or "syrup" in lower_line:
        route = "oral (syrup)"

    # 2. Extract dosage (amount & unit)
    # Check formulation / parenthesized dosage first: e.g. Tablet Pan (40 mg), Tablet Switch CV (325 mg), (0.5 ml)
    m_form_dose = re.search(
        r"\b(?:Tablet|Capsule|Injection|Syrup|Tab|Cap|Inj)\.?\s*[A-Za-z0-9\s\+\-]+\s*\(\s*(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|ml)?\s*\)",
        line,
        re.IGNORECASE,
    )
    m_paren_dose = re.search(
        r"\(\s*(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|ml)?\s*\)",
        line,
        re.IGNORECASE,
    )
    dosage_match = DOSAGE_RE.search(line)

    if m_form_dose:
        try:
            val = float(m_form_dose.group("amount"))
            unit = m_form_dose.group("unit") or ("ml" if route == "injection" or val < 1 else "mg")
            dosage_unit = unit.lower()
            dosage_amount = 1 if val < 1 else int(round(val))
            dosage_needs_review = val < 1
        except ValueError:
            dosage_amount = 1
            dosage_unit = "mg"
            dosage_needs_review = True
    elif m_paren_dose and m_paren_dose.group("unit"):
        try:
            val = float(m_paren_dose.group("amount"))
            dosage_unit = m_paren_dose.group("unit").lower()
            dosage_amount = 1 if val < 1 else int(round(val))
            dosage_needs_review = val < 1
        except ValueError:
            dosage_amount = 1
            dosage_unit = "mg"
            dosage_needs_review = True
    elif dosage_match:
        try:
            val = float(dosage_match.group("amount"))
            dosage_unit = dosage_match.group("unit").lower()
            dosage_amount = 1 if val < 1 else int(round(val))
            dosage_needs_review = val < 1
        except ValueError:
            dosage_amount = 1
            dosage_unit = "mg"
            dosage_needs_review = True
    else:
        # Fallback for unitless counts (e.g. Capsule Vizylac Rich)
        standalone_num = re.search(r"\b(\d+)\b", line)
        dosage_amount = int(standalone_num.group(1)) if standalone_num else 1
        if "cap" in lower_line:
            dosage_unit = "capsule"
            dosage_needs_review = False
        elif "tab" in lower_line:
            dosage_unit = "tablet"
            dosage_needs_review = False
        else:
            dosage_unit = "mg"
            dosage_needs_review = True

    # 3. Extract duration
    duration_match = DURATION_RE.search(line)
    if duration_match:
        val = int(duration_match.group("num"))
        u = duration_match.group("unit").lower()
        if "week" in u:
            duration_days = val * 7
        elif "month" in u:
            duration_days = val * 30
        else:
            duration_days = val
    elif "stat" in lower_line:
        duration_days = 1
    else:
        duration_days = 7

    # 4. Frequency, Shorthand & Timing resolution
    frequency_per_day = 1
    suggested_times = ["08:00"]
    with_food = False
    empty_stomach = False
    bedtime_only = False
    notes_parts = []
    frequency_needs_review = True
    times_needs_review = False

    # Check numeric shorthand (e.g. 1-0-1, 1-1-1, 0-0-1, 1/2-1/2-1/2)
    numeric_found = None
    for pattern, info in NUMERIC_SHORTHAND_MAP.items():
        if re.search(rf"(?:^|\s){re.escape(pattern)}(?:\s|$)", line):
            numeric_found = (pattern, info)
            break

    if numeric_found:
        pat, info = numeric_found
        frequency_per_day = info["frequency_per_day"]
        suggested_times = list(info["suggested_times"])
        with_food = info.get("with_food", False)
        empty_stomach = info.get("empty_stomach", False)
        bedtime_only = info.get("bedtime_only", False)
        frequency_needs_review = False
        times_needs_review = info.get("needs_review_time", False)
        notes_parts.append(f"Shorthand: {pat} ({info.get('description', '')})")
    else:
        # Check Latin frequency abbreviations (e.g. BD, TID, OD, HS, SOS, STAT)
        latin_found = None
        for abbr, info in LATIN_FREQUENCY_MAP.items():
            if re.search(rf"\b{re.escape(abbr)}\b", lower_line):
                latin_found = (abbr, info)
                break

        if latin_found:
            abbr, info = latin_found
            frequency_per_day = info["frequency_per_day"]
            suggested_times = list(info["suggested_times"])
            bedtime_only = info.get("bedtime_only", False)
            frequency_needs_review = False
            times_needs_review = info.get("needs_review_time", False)
            if "notes" in info:
                notes_parts.append(info["notes"])
            else:
                notes_parts.append(f"Frequency: {abbr.upper()}")

    # Check meal condition modifiers (e.g. before breakfast, after dinner, ac, pc)
    for mod, mod_info in MEAL_MODIFIER_MAP.items():
        if re.search(rf"\b{re.escape(mod)}\b", lower_line):
            if mod_info.get("with_food"):
                with_food = True
            if mod_info.get("empty_stomach"):
                empty_stomach = True
            notes_parts.append(mod_info.get("description", ""))
            break

    # 5. Isolate Drug Name candidate and Fuzzy Match via RapidFuzz
    # Try brand extraction directly following dosage form prefix (Tablet, Capsule, etc.)
    m_brand = re.search(
        r"\b(?:Tablet|Capsule|Injection|Syrup|Tab|Cap|Inj)\.?\s+([A-Za-z0-9\s\+\-]+?)(?:\s*\(|\s+\d+\s*(?:mg|ml)|\s+(?:1-|0-|1/2|stat|x\s*\d|for\s*\d|\d+\s*days?)|$)",
        line,
        re.IGNORECASE,
    )
    cand_brand = m_brand.group(1).strip() if m_brand else ""

    best_drug = None
    best_score = 0.0

    # Priority 1: Match isolated brand candidate against COMMON_DRUG_NAMES
    if cand_brand and len(cand_brand) >= 2:
        match = process.extractOne(
            cand_brand,
            COMMON_DRUG_NAMES,
            scorer=fuzz.token_sort_ratio,
        )
        if match and match[1] >= 80.0:
            best_drug = match[0]
            best_score = match[1]
        else:
            for entry in COMMON_DRUG_NAMES:
                score = fuzz.partial_ratio(entry.lower(), cand_brand.lower())
                if score > best_score and score >= 80.0:
                    best_score = score
                    best_drug = entry

    # Priority 2: Scan full line for active ingredient / brand matches in drug catalog
    if not best_drug or best_score < 85.0:
        for entry in COMMON_DRUG_NAMES:
            score = fuzz.partial_ratio(entry.lower(), lower_line)
            if score > best_score and score >= 80.0:
                best_score = score
                best_drug = entry

    # Fallback 1: If brand candidate exists, keep it as candidate name
    if not best_drug and cand_brand and len(cand_brand) >= 3:
        best_drug = cand_brand.title()
        best_score = 65.0

    # Fallback 2: Token extraction from cleaned line
    if not best_drug:
        cleaned = _clean_line_candidate(line)
        cleaned = DOSAGE_RE.sub("", cleaned)
        cleaned = DURATION_RE.sub("", cleaned)
        for p in list(NUMERIC_SHORTHAND_MAP.keys()) + list(LATIN_FREQUENCY_MAP.keys()) + list(MEAL_MODIFIER_MAP.keys()):
            cleaned = re.sub(rf"\b{re.escape(p)}\b", "", cleaned, flags=re.IGNORECASE)

        drug_token = re.sub(r"[^\w\s]", " ", cleaned).strip()
        drug_words = drug_token.split()
        if not drug_words:
            return None

        candidate_name = " ".join(drug_words[:2]) if len(drug_words) >= 2 else drug_words[0]
        best_match = process.extractOne(
            candidate_name,
            COMMON_DRUG_NAMES,
            scorer=fuzz.token_sort_ratio,
        )
        if best_match:
            best_drug = best_match[0] if best_match[1] >= 70.0 else candidate_name.capitalize()
            best_score = best_match[1]
        else:
            best_drug = candidate_name.capitalize()
            best_score = 0.0

    if best_score < 50.0 and dosage_needs_review and frequency_needs_review:
        return None

    drug_name_needs_review = best_score < 80.0

    needs_review = {
        "drug_name": drug_name_needs_review,
        "dosage": dosage_needs_review,
        "frequency": frequency_needs_review,
        "times": times_needs_review,
    }

    return ParsedMedicationCandidate(
        raw_text_snippet=line,
        matched_drug_name=best_drug,
        match_confidence=round(float(best_score), 1),
        dosage_amount=dosage_amount,
        dosage_unit=dosage_unit,
        frequency_per_day=frequency_per_day,
        suggested_times=suggested_times,
        duration_days=duration_days,
        route=route,
        with_food=with_food,
        empty_stomach=empty_stomach,
        bedtime_only=bedtime_only,
        notes="; ".join(notes_parts) if notes_parts else None,
        needs_review=needs_review,
    )


def parse_prescription_text(raw_text: str) -> List[ParsedMedicationCandidate]:
    """Parses raw OCR extracted text into a list of unique medication candidates."""
    lines = raw_text.splitlines()
    candidates: List[ParsedMedicationCandidate] = []
    seen_names = set()

    for line in lines:
        cand = parse_line_for_medication(line)
        if cand:
            name_key = cand.matched_drug_name.lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                candidates.append(cand)

    return candidates


def parse_prescription_file(file_bytes: bytes, filename: str) -> PrescriptionParseResponse:
    """
    Extracts text from uploaded prescription document (PDF or image)
    and parses medication candidates with abbreviation resolution and RapidFuzz matching.
    """
    raw_text = extract_text_from_pdf_or_image(file_bytes, filename)
    if not raw_text or not raw_text.strip():
        return PrescriptionParseResponse(
            success=False,
            raw_text="",
            candidates=[],
            total_found=0,
        )

    candidates = parse_prescription_text(raw_text)
    return PrescriptionParseResponse(
        success=len(candidates) > 0,
        raw_text=raw_text,
        candidates=candidates,
        total_found=len(candidates),
    )
