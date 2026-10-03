from app.services.prescription_parser import parse_line_for_medication

def run_matrix():
    test_cases = [
        ("Tab. Metfornin 500mg 1-0-1 pc", "Metformin"),
        ("Cap. Azythromycin 250 mg OD", "Azithromycin"),
        ("Tab Pantoprazol 40mg BB / AC", "Pantoprazole"),
        ("Tab Atorvasttin 10mg HS", "Atorvastatin"),
        ("Tab Amoxyclav 625mg BD", "Amoxicillin and Clavulanate"),
        ("Tab Telmisartn 40mg OD", "Telmisartan"),
        ("Tab Cetrizine 10mg HS", "Cetirizine"),
        ("Tab Paracetamol 650mg SOS", "Paracetamol"),
    ]

    header = f"{'INPUT SNIPPET':<32} | {'MATCHED DRUG':<22} | {'SCORE':<7} | {'REVIEW DRUG':<12} | {'REVIEW TIMES':<12}"
    print(header)
    print("-" * len(header))

    for snippet, expected in test_cases:
        res = parse_line_for_medication(snippet)
        if res:
            drug = res.matched_drug_name
            score = f"{res.match_confidence}%"
            rev_drug = str(res.needs_review["drug_name"])
            rev_times = str(res.needs_review["times"])
            print(f"{snippet:<32} | {drug:<22} | {score:>7} | {rev_drug:<12} | {rev_times:<12}")
        else:
            print(f"{snippet:<32} | {'NO MATCH':<22} | {'0.0%':>7} | {'True':<12} | {'False':<12}")

if __name__ == "__main__":
    run_matrix()
