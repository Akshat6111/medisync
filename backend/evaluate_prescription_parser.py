"""
MediSync Prescription Parser Evaluation Suite
=============================================
Evaluates `app/services/prescription_parser.py` against 10 synthetic test cases
(5 digital text, 5 image-rendered with OCR).

Compares extracted candidates against ground truth:
- Extraction detection (medication identified vs total expected)
- Drug name match accuracy
- Frequency parsing accuracy
- Dosage parsing accuracy
- Detailed failure analysis explaining root causes
"""

import io
import os
import sys
from typing import List, Dict, Any, Tuple
from rapidfuzz import fuzz
from PIL import Image, ImageDraw, ImageFilter

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.prescription_parser import (
    parse_prescription_text,
    parse_prescription_file,
)


def render_prescription_image(lines: List[str], spacing: int = 55, blur: bool = False) -> bytes:
    """Renders text lines into a high-contrast synthetic prescription PNG image."""
    height = 90 + len(lines) * spacing
    img = Image.new("RGB", (900, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 35
    for line in lines:
        draw.text((45, y), line, fill=(20, 20, 20))
        y += spacing

    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def normalize_str(s: str) -> str:
    return s.strip().lower()


def evaluate_case(
    case_id: int,
    description: str,
    case_type: str,
    raw_input_data: Any,
    ground_truth: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Runs parser on a single case and matches extracted candidates to ground truth.
    """
    if case_type == "Digital Text":
        extracted_candidates = parse_prescription_text(raw_input_data)
        raw_ocr_text = raw_input_data.strip()
    else:
        # Image rendered
        parse_response = parse_prescription_file(raw_input_data, f"case_{case_id}.png")
        extracted_candidates = parse_response.candidates
        raw_ocr_text = parse_response.raw_text.strip()

    total_expected = len(ground_truth)
    total_extracted = len(extracted_candidates)

    correct_drugs = 0
    correct_frequencies = 0
    correct_dosages = 0
    full_matches = 0
    failures = []

    # Greedy matching of extracted candidates to ground truth items
    used_candidate_indices = set()

    for gt in ground_truth:
        expected_drug = gt["drug_name"]
        expected_dosage = gt["dosage_amount"]
        expected_unit = gt["dosage_unit"].lower()
        expected_freq = gt["frequency_per_day"]

        best_cand_idx = None
        best_score = 0.0

        for idx, cand in enumerate(extracted_candidates):
            if idx in used_candidate_indices:
                continue
            cand_name = cand.matched_drug_name
            score = fuzz.token_sort_ratio(normalize_str(expected_drug), normalize_str(cand_name))
            if score > best_score and score >= 60.0:
                best_score = score
                best_cand_idx = idx

        if best_cand_idx is not None:
            used_candidate_indices.add(best_cand_idx)
            cand = extracted_candidates[best_cand_idx]

            drug_matched = best_score >= 85.0
            freq_matched = cand.frequency_per_day == expected_freq
            dosage_matched = (
                cand.dosage_amount == expected_dosage
                and cand.dosage_unit.lower() == expected_unit
            )

            if drug_matched:
                correct_drugs += 1
            else:
                failures.append(
                    f"Drug name mismatch for '{expected_drug}': OCR/RapidFuzz extracted '{cand.matched_drug_name}' (similarity {best_score:.1f}%)"
                )

            if freq_matched:
                correct_frequencies += 1
            else:
                failures.append(
                    f"Frequency mismatch for '{expected_drug}': expected {expected_freq}/day, extracted {cand.frequency_per_day}/day"
                )

            if dosage_matched:
                correct_dosages += 1
            else:
                failures.append(
                    f"Dosage mismatch for '{expected_drug}': expected {expected_dosage} {expected_unit}, extracted {cand.dosage_amount} {cand.dosage_unit}"
                )

            if drug_matched and freq_matched:
                full_matches += 1
        else:
            failures.append(f"Missing extraction: '{expected_drug}' was not detected in prescription text/image.")

    # Check for extraneous hallucinated or false-positive extractions
    if total_extracted > total_expected:
        extra_count = total_extracted - len(used_candidate_indices)
        if extra_count > 0:
            failures.append(f"Spurious extraction: {extra_count} extra candidate(s) detected.")

    return {
        "case_id": case_id,
        "description": description,
        "case_type": case_type,
        "expected_count": total_expected,
        "extracted_count": total_extracted,
        "full_matches": full_matches,
        "correct_drugs": correct_drugs,
        "correct_frequencies": correct_frequencies,
        "correct_dosages": correct_dosages,
        "failures": failures,
        "raw_ocr_snippet": raw_ocr_text.replace("\n", " // ")[:75] + ("..." if len(raw_ocr_text) > 75 else ""),
    }


def main():
    cases_config = [
        # 1. Digital Text Cases
        {
            "case_id": 1,
            "description": "Standard Chronic Regimen (1-0-1, 0-0-1 hs)",
            "type": "Digital Text",
            "input": (
                "Dr. Sharma Clinic - OPD Slip\n"
                "Rx:\n"
                "1. Tab Metformin 500mg 1-0-1 pc x 15 days\n"
                "2. Tab Atorvastatin 20mg 0-0-1 hs x 30 days\n"
            ),
            "ground_truth": [
                {"drug_name": "Metformin", "dosage_amount": 500, "dosage_unit": "mg", "frequency_per_day": 2},
                {"drug_name": "Atorvastatin", "dosage_amount": 20, "dosage_unit": "mg", "frequency_per_day": 1},
            ],
        },
        {
            "case_id": 2,
            "description": "Acute Infection & Analgesic (TDS, SOS)",
            "type": "Digital Text",
            "input": (
                "City Health Center\n"
                "Rx:\n"
                "1. Cap Amoxicillin 500mg TDS x 5 days\n"
                "2. Tab Paracetamol 650mg SOS after food\n"
            ),
            "ground_truth": [
                {"drug_name": "Amoxicillin", "dosage_amount": 500, "dosage_unit": "mg", "frequency_per_day": 3},
                {"drug_name": "Paracetamol", "dosage_amount": 650, "dosage_unit": "mg", "frequency_per_day": 1},
            ],
        },
        {
            "case_id": 3,
            "description": "Phonetic Spelling Typos in Indian Brands",
            "type": "Digital Text",
            "input": (
                "Rx:\n"
                "1. Tab Pantoprazol 40mg 1-0-0 bb\n"
                "2. Tab Telmisartn 40mg OD\n"
            ),
            "ground_truth": [
                {"drug_name": "Pantoprazole", "dosage_amount": 40, "dosage_unit": "mg", "frequency_per_day": 1},
                {"drug_name": "Telmisartan", "dosage_amount": 40, "dosage_unit": "mg", "frequency_per_day": 1},
            ],
        },
        {
            "case_id": 4,
            "description": "Combination Brand & Bedtime Sig",
            "type": "Digital Text",
            "input": (
                "Rx:\n"
                "1. Tab Augmentin 625mg BD x 7 days\n"
                "2. Tab Cetirizine 10mg HS\n"
            ),
            "ground_truth": [
                {"drug_name": "Augmentin", "dosage_amount": 625, "dosage_unit": "mg", "frequency_per_day": 2},
                {"drug_name": "Cetirizine", "dosage_amount": 10, "dosage_unit": "mg", "frequency_per_day": 1},
            ],
        },
        {
            "case_id": 5,
            "description": "Non-Standard Phrasing & Multi-Strength Compound",
            "type": "Digital Text",
            "input": (
                "Rx:\n"
                "1. Take 1 tab Aspirin 75mg daily morning\n"
                "2. Syp Ascoril LS 5ml TDS\n"
                "3. Tab Glycomet-GP 1/850 1-0-1\n"
            ),
            "ground_truth": [
                {"drug_name": "Aspirin", "dosage_amount": 75, "dosage_unit": "mg", "frequency_per_day": 1},
                {"drug_name": "Ascoril Ls", "dosage_amount": 5, "dosage_unit": "ml", "frequency_per_day": 3},
                {"drug_name": "Glycomet", "dosage_amount": 1, "dosage_unit": "tablet", "frequency_per_day": 2},
            ],
        },

        # 2. Image-Rendered Cases (OCR)
        {
            "case_id": 6,
            "description": "Image: High-Resolution Slip (OD, BD)",
            "type": "Image (OCR)",
            "input": render_prescription_image([
                "Dr. Mehta Clinic",
                "Rx:",
                "1. Tab Amlodipine 5mg OD",
                "2. Tab Metoprolol 50mg BD",
            ], spacing=55),
            "ground_truth": [
                {"drug_name": "Amlodipine", "dosage_amount": 5, "dosage_unit": "mg", "frequency_per_day": 1},
                {"drug_name": "Metoprolol", "dosage_amount": 50, "dosage_unit": "mg", "frequency_per_day": 2},
            ],
        },
        {
            "case_id": 7,
            "description": "Image: Numeric Matrix Shorthand (1-0-1, 1-0-0)",
            "type": "Image (OCR)",
            "input": render_prescription_image([
                "Dr. Sharma Clinic",
                "Rx:",
                "1. Tab Ciprofloxacin 500mg 1-0-1",
                "2. Cap Omeprazole 20mg 1-0-0",
            ], spacing=55),
            "ground_truth": [
                {"drug_name": "Ciprofloxacin", "dosage_amount": 500, "dosage_unit": "mg", "frequency_per_day": 2},
                {"drug_name": "Omeprazole", "dosage_amount": 20, "dosage_unit": "mg", "frequency_per_day": 1},
            ],
        },
        {
            "case_id": 8,
            "description": "Image: Parenthesized Dosage & Duration",
            "type": "Image (OCR)",
            "input": render_prescription_image([
                "City Hospital OPD",
                "Rx:",
                "1. Tablet Azithromycin 500mg OD x 3 days",
                "2. Tablet Montelukast 10mg HS",
            ], spacing=55),
            "ground_truth": [
                {"drug_name": "Azithromycin", "dosage_amount": 500, "dosage_unit": "mg", "frequency_per_day": 1},
                {"drug_name": "Montelukast", "dosage_amount": 10, "dosage_unit": "mg", "frequency_per_day": 1},
            ],
        },
        {
            "case_id": 9,
            "description": "Image: Multi-Drug Infection Regimen (BD, TDS)",
            "type": "Image (OCR)",
            "input": render_prescription_image([
                "Rx:",
                "1. Tab Doxycycline 100mg BD x 7 days",
                "2. Tab Ibuprofen 400mg TDS",
            ], spacing=55),
            "ground_truth": [
                {"drug_name": "Doxycycline", "dosage_amount": 100, "dosage_unit": "mg", "frequency_per_day": 2},
                {"drug_name": "Ibuprofen", "dosage_amount": 400, "dosage_unit": "mg", "frequency_per_day": 3},
            ],
        },
        {
            "case_id": 10,
            "description": "Image: Blurred / Optical Degradation Challenge",
            "type": "Image (OCR)",
            "input": render_prescription_image([
                "Dr. Gupta Clinic",
                "Rx:",
                "1. Tab Cefixime 200mg BD x 5 days",
                "2. Tab Ranitidine 150mg BD",
            ], spacing=55, blur=True),
            "ground_truth": [
                {"drug_name": "Cefixime", "dosage_amount": 200, "dosage_unit": "mg", "frequency_per_day": 2},
                {"drug_name": "Ranitidine", "dosage_amount": 150, "dosage_unit": "mg", "frequency_per_day": 2},
            ],
        },
    ]

    print("=" * 105)
    print("           MEDISYNC RXPARSE EVALUATION REPORT (SYNTHETIC SAMPLES)")
    print("=" * 105)
    print("NOTE: All samples are synthetically generated test fixtures, not real patient data.\n")

    results = []
    total_expected_all = 0
    total_extracted_all = 0
    total_drugs_all = 0
    total_freq_all = 0
    total_dosage_all = 0
    total_full_all = 0

    for cfg in cases_config:
        res = evaluate_case(
            case_id=cfg["case_id"],
            description=cfg["description"],
            case_type=cfg["type"],
            raw_input_data=cfg["input"],
            ground_truth=cfg["ground_truth"],
        )
        results.append(res)

        total_expected_all += res["expected_count"]
        total_extracted_all += res["extracted_count"]
        total_drugs_all += res["correct_drugs"]
        total_freq_all += res["correct_frequencies"]
        total_dosage_all += res["correct_dosages"]
        total_full_all += res["full_matches"]

    # Print Table
    header = (
        f"{'Case':<5} | {'Type':<12} | {'Description':<32} | "
        f"{'Extr/Exp':<9} | {'Drug Match':<11} | {'Freq Match':<11} | {'Status'}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        status = "PASS" if not r["failures"] else "FAIL"
        extr_str = f"{r['extracted_count']}/{r['expected_count']}"
        drug_str = f"{r['correct_drugs']}/{r['expected_count']}"
        freq_str = f"{r['correct_frequencies']}/{r['expected_count']}"
        print(
            f"{r['case_id']:<5} | "
            f"{r['case_type']:<12} | "
            f"{r['description'][:32]:<32} | "
            f"{extr_str:<9} | "
            f"{drug_str:<11} | "
            f"{freq_str:<11} | "
            f"{status}"
        )

    print("-" * len(header))

    # Summary Line
    drug_pct = (total_drugs_all / total_expected_all) * 100.0
    freq_pct = (total_freq_all / total_expected_all) * 100.0
    full_pct = (total_full_all / total_expected_all) * 100.0

    print(
        f"\nSUMMARY: Extracted {total_extracted_all}/{total_expected_all} medications | "
        f"Drug-Name Match Rate: {total_drugs_all}/{total_expected_all} ({drug_pct:.1f}%) | "
        f"Frequency Accuracy: {total_freq_all}/{total_expected_all} ({freq_pct:.1f}%) | "
        f"Fully Correct: {total_full_all}/{total_expected_all} ({full_pct:.1f}%)\n"
    )

    # Detailed Failure Analysis
    print("=" * 105)
    print("                             DETAILED FAILURE ANALYSIS")
    print("=" * 105)
    any_failures = False
    for r in results:
        if r["failures"]:
            any_failures = True
            print(f"\n[Case {r['case_id']}] {r['description']} ({r['case_type']}):")
            print(f"  Snippet: {r['raw_ocr_snippet']}")
            for f in r["failures"]:
                print(f"  x {f}")

    if not any_failures:
        print("No failures encountered.")
    print("=" * 105)


if __name__ == "__main__":
    main()
