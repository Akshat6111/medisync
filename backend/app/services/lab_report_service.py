import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.llm import get_llm
from app.models.lab_report import LabReport, LabReportFlag, LabReportStatus, LabReportValue
from app.services.lab_report_parser import (
    extract_text_from_pdf_or_image,
    parse_lab_report_text,
)

logger = logging.getLogger(__name__)


def generate_plain_language_summary(structured_entries: List[dict]) -> str:
    """
    Generates a patient-friendly summary grounded strictly in the extracted structured values.
    Never invents or speculates beyond the provided tests.
    """
    if not structured_entries:
        return (
            "We could not extract structured test values from this report format. "
            "Please verify that the document is legible or try uploading a clearer digital copy."
        )

    # Format structured items into a clean representation
    table_lines = []
    for entry in structured_entries:
        ref_text = "Unknown"
        if entry["reference_low"] is not None and entry["reference_high"] is not None:
            ref_text = f"{entry['reference_low']} - {entry['reference_high']}"
        elif entry["reference_low"] is not None:
            ref_text = f"> {entry['reference_low']}"
        elif entry["reference_high"] is not None:
            ref_text = f"< {entry['reference_high']}"

        table_lines.append(
            f"- Test: {entry['test_name']} | Result: {entry['value']} {entry['unit']} | "
            f"Reference Range: {ref_text} | Status: {entry['flag'].upper()}"
        )

    formatted_values = "\n".join(table_lines)

    system_instruction = (
        "You are MediSync's clinical report summarizer. "
        "Your task is to summarize the provided laboratory results in plain, patient-friendly language.\n\n"
        "STRICT CONSTRAINTS:\n"
        "1. Base your summary ONLY on the structured test entries provided below.\n"
        "2. NEVER invent, assume, or speculate about tests, values, or diagnoses not explicitly present.\n"
        "3. Explicitly mention which tests are within normal limits, and clearly highlight any that are HIGH or LOW.\n"
        "4. Explain in plain terms what each extracted test measures, but avoid providing medical treatment plans.\n"
        "5. Keep the tone calm, professional, and clear."
    )

    user_prompt = (
        f"Here are the extracted structured laboratory test results:\n\n"
        f"{formatted_values}\n\n"
        "Please provide a clear, structured plain-language summary for the patient."
    )

    client = get_llm()
    models_to_try = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
        except Exception as e:
            logger.warning("LLM summarization failed with model %s: %s", model_name, e)
            continue

    # Fallback summary if LLM call fails
    normal_count = sum(1 for e in structured_entries if e["flag"] == "normal")
    high_count = sum(1 for e in structured_entries if e["flag"] == "high")
    low_count = sum(1 for e in structured_entries if e["flag"] == "low")
    return (
        f"Summary generated from {len(structured_entries)} extracted tests: "
        f"{normal_count} in normal range, {high_count} high, {low_count} low. "
        "Detailed test values are listed in the table below."
    )


def create_and_process_lab_report(
    db: Session,
    patient_id: UUID,
    filename: str,
    file_bytes: bytes,
) -> LabReport:
    """
    Saves lab_report row with status processing, extracts raw text,
    runs regex parsing, classifies flags, generates LLM summary, and commits.
    """
    report = LabReport(
        patient_id=patient_id,
        original_filename=filename,
        status=LabReportStatus.PROCESSING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        # Step 1: Text extraction
        raw_text = extract_text_from_pdf_or_image(file_bytes, filename)
        report.raw_text = raw_text

        # Step 2: Regex structured parsing
        parsed_entries = parse_lab_report_text(raw_text)

        # Step 3: Save values
        for item in parsed_entries:
            val_record = LabReportValue(
                report_id=report.id,
                test_name=item["test_name"],
                value=item["value"],
                unit=item["unit"],
                reference_low=item["reference_low"],
                reference_high=item["reference_high"],
                flag=LabReportFlag(item["flag"]),
            )
            db.add(val_record)

        # Step 4: Generate LLM summary grounded in structured values
        summary = generate_plain_language_summary(parsed_entries)
        report.summary = summary
        report.status = LabReportStatus.COMPLETED

        db.commit()
        db.refresh(report)
        return report

    except Exception as e:
        logger.error("Failed to process lab report %s: %s", report.id, e, exc_info=True)
        report.status = LabReportStatus.FAILED
        report.summary = f"Processing failed: {str(e)}"
        db.commit()
        db.refresh(report)
        return report


def get_reports_by_patient(db: Session, patient_id: UUID) -> List[LabReport]:
    return (
        db.query(LabReport)
        .filter(LabReport.patient_id == patient_id)
        .order_by(LabReport.uploaded_at.desc())
        .all()
    )


def get_report_by_id(db: Session, report_id: UUID, patient_id: UUID) -> Optional[LabReport]:
    return (
        db.query(LabReport)
        .filter(LabReport.id == report_id, LabReport.patient_id == patient_id)
        .first()
    )


def delete_lab_report(db: Session, report_id: UUID, patient_id: UUID) -> bool:
    report = get_report_by_id(db, report_id, patient_id)
    if not report:
        return False
    db.delete(report)
    db.commit()
    return True
