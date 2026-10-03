from app.services.prescription_parser import parse_prescription_text

def test_rx_parser():
    sample_prescription_text = """
    Dr. Sharma's Clinic - General Medicine
    Rx:
    1. Tab. Metfornin 500mg 1-0-1 pc x 15 days
    2. Cap. Azythromycin 250 mg OD x 3 days
    3. Tab Pantoprazol 40mg BB / AC for 10 days
    4. Tab Paracetamol 650mg SOS after food
    5. Tab Clonazepam 0.5mg HS
    6. Random non-med line for patient rest
    """

    print("--- Testing RxParse Shorthand & Fuzzy Matching ---")
    candidates = parse_prescription_text(sample_prescription_text)
    print(f"Total candidates detected: {len(candidates)}\n")

    for i, c in enumerate(candidates, 1):
        print(f"[{i}] Snippet: '{c.raw_text_snippet}'")
        print(f"    Matched Drug: {c.matched_drug_name} (Confidence: {c.match_confidence}%)")
        print(f"    Dose: {c.dosage_amount} {c.dosage_unit} | Freq: {c.frequency_per_day}/day | Times: {c.suggested_times}")
        print(f"    Conditions: Food={c.with_food}, EmptyStomach={c.empty_stomach}, Bedtime={c.bedtime_only}")
        print(f"    Needs Review: {c.needs_review}")
        print()

    # Assertions
    names = [c.matched_drug_name for c in candidates]
    assert "Metformin" in names, "Metfornin should fuzzy match to Metformin"
    assert "Azithromycin" in names, "Azythromycin should fuzzy match to Azithromycin"
    assert "Pantoprazole" in names, "Pantoprazol should fuzzy match to Pantoprazole"
    assert "Paracetamol" in names, "Paracetamol should match"
    assert "Clonazepam" in names, "Clonazepam should match"

    # Verify hs bedtime flags review
    clonazepam_cand = next(c for c in candidates if c.matched_drug_name == "Clonazepam")
    assert clonazepam_cand.needs_review["times"] is True, "HS bedtime should be flagged for review"

    print("All RxParse unit assertions passed successfully!")

if __name__ == "__main__":
    test_rx_parser()
