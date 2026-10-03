import os
from app.services.lab_report_parser import extract_text_from_pdf_or_image, parse_lab_report_text
from app.services.lab_report_service import generate_plain_language_summary

pdf_path = os.path.join(os.path.dirname(__file__), "sample_lab_report.pdf")
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

print("--- 1. TEXT EXTRACTION ---")
raw_text = extract_text_from_pdf_or_image(pdf_bytes, "sample_lab_report.pdf")
print(f"Extracted {len(raw_text)} characters.")
print("Sample of extracted text:")
print("\n".join(raw_text.splitlines()[:15]))
print("...")

print("\n--- 2. STRUCTURED REGEX PARSING ---")
entries = parse_lab_report_text(raw_text)
print(f"Parsed {len(entries)} structured test entries:")
for e in entries:
    ref = f"{e['reference_low']} - {e['reference_high']}" if e['reference_low'] is not None and e['reference_high'] is not None else (f"< {e['reference_high']}" if e['reference_high'] is not None else f"> {e['reference_low']}")
    print(f"  • {e['test_name']:<24} = {e['value']:<6} {e['unit']:<8} (Ref: {ref:<13}) -> FLAG: {e['flag'].upper()}")

print("\n--- 3. LLM GROUNDED SUMMARY GENERATION ---")
summary = generate_plain_language_summary(entries)
print("Summary output:")
print(summary)
