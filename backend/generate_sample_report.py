"""
Generates a realistic sample medical laboratory report PDF for testing ReportBrief.
"""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

output_pdf_path = os.path.join(os.path.dirname(__file__), "sample_lab_report.pdf")

doc = SimpleDocTemplate(
    output_pdf_path,
    pagesize=letter,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40,
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Heading1"],
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#1e3a8a"),
    alignment=1, # Center
)
subtitle_style = ParagraphStyle(
    "DocSubtitle",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#64748b"),
    alignment=1,
)
meta_label_style = ParagraphStyle(
    "MetaLabel",
    parent=styles["Normal"],
    fontSize=9,
    leading=12,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor("#334155"),
)
meta_value_style = ParagraphStyle(
    "MetaValue",
    parent=styles["Normal"],
    fontSize=9,
    leading=12,
    textColor=colors.HexColor("#1e293b"),
)

story = []

# Hospital / Diagnostic Center Header
story.append(Paragraph("APEX HEALTH PATHOLOGY & DIAGNOSTIC LABS", title_style))
story.append(Paragraph("102 Medical Boulevard, Suite 400 • CLIA ID: 99D0876543", subtitle_style))
story.append(Spacer(1, 15))

# Patient Metadata Table
patient_info_data = [
    [
        Paragraph("Patient Name:", meta_label_style),
        Paragraph("Jane Doe", meta_value_style),
        Paragraph("Date of Collection:", meta_label_style),
        Paragraph("2026-09-06 08:30 AM", meta_value_style),
    ],
    [
        Paragraph("Patient ID / MRN:", meta_label_style),
        Paragraph("MED-884920", meta_value_style),
        Paragraph("Report Date:", meta_label_style),
        Paragraph("2026-09-07 02:15 PM", meta_value_style),
    ],
    [
        Paragraph("Age / Gender:", meta_label_style),
        Paragraph("42 Y / Female", meta_value_style),
        Paragraph("Ordering Physician:", meta_label_style),
        Paragraph("Dr. Sarah Jenkins, MD", meta_value_style),
    ],
]

info_table = Table(patient_info_data, colWidths=[95, 170, 115, 150])
info_table.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
)
story.append(info_table)
story.append(Spacer(1, 20))

# Test Results Section Header
story.append(Paragraph("COMPREHENSIVE METABOLIC & HEMATOLOGY PANEL", ParagraphStyle(
    "SectionHead",
    parent=styles["Heading2"],
    fontSize=12,
    leading=16,
    textColor=colors.HexColor("#0f172a"),
    fontName="Helvetica-Bold",
)))
story.append(Spacer(1, 8))

# Test Results Table
# Format: Test Name | Result | Unit | Reference Range | Status Flag
table_header_style = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontSize=9,
    fontName="Helvetica-Bold",
    textColor=colors.white,
)
cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold")
cell_normal = ParagraphStyle("CellNormal", parent=styles["Normal"], fontSize=9)
cell_high = ParagraphStyle("CellHigh", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#dc2626"))
cell_low = ParagraphStyle("CellLow", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#d97706"))

test_rows = [
    [
        Paragraph("Test Name", table_header_style),
        Paragraph("Result", table_header_style),
        Paragraph("Unit", table_header_style),
        Paragraph("Reference Interval", table_header_style),
        Paragraph("Status", table_header_style),
    ],
    # 1. Hemoglobin (Low)
    [
        Paragraph("Hemoglobin", cell_bold),
        Paragraph("10.8", cell_low),
        Paragraph("g/dL", cell_normal),
        Paragraph("12.0 - 15.5", cell_normal),
        Paragraph("LOW", cell_low),
    ],
    # 2. Fasting Blood Glucose (High)
    [
        Paragraph("Fasting Blood Glucose", cell_bold),
        Paragraph("118.0", cell_high),
        Paragraph("mg/dL", cell_normal),
        Paragraph("70 - 99", cell_normal),
        Paragraph("HIGH", cell_high),
    ],
    # 3. Total Cholesterol (High)
    [
        Paragraph("Total Cholesterol", cell_bold),
        Paragraph("224.0", cell_high),
        Paragraph("mg/dL", cell_normal),
        Paragraph("< 200", cell_normal),
        Paragraph("HIGH", cell_high),
    ],
    # 4. HDL Cholesterol (Normal)
    [
        Paragraph("HDL Cholesterol", cell_bold),
        Paragraph("52.0", cell_normal),
        Paragraph("mg/dL", cell_normal),
        Paragraph("> 40", cell_normal),
        Paragraph("NORMAL", cell_normal),
    ],
    # 5. Serum Creatinine (Normal)
    [
        Paragraph("Serum Creatinine", cell_bold),
        Paragraph("0.85", cell_normal),
        Paragraph("mg/dL", cell_normal),
        Paragraph("0.50 - 1.10", cell_normal),
        Paragraph("NORMAL", cell_normal),
    ],
    # 6. Thyroid Stimulating Hormone (Normal)
    [
        Paragraph("TSH", cell_bold),
        Paragraph("2.45", cell_normal),
        Paragraph("uIU/mL", cell_normal),
        Paragraph("0.40 - 4.50", cell_normal),
        Paragraph("NORMAL", cell_normal),
    ],
    # 7. Platelet Count (Normal)
    [
        Paragraph("Platelet Count", cell_bold),
        Paragraph("245", cell_normal),
        Paragraph("10^3/uL", cell_normal),
        Paragraph("150 - 450", cell_normal),
        Paragraph("NORMAL", cell_normal),
    ],
    # 8. White Blood Cell Count (Normal)
    [
        Paragraph("WBC", cell_bold),
        Paragraph("6.8", cell_normal),
        Paragraph("10^3/uL", cell_normal),
        Paragraph("4.5 - 11.0", cell_normal),
        Paragraph("NORMAL", cell_normal),
    ],
    # 9. Glycated Hemoglobin (HbA1c) (High)
    [
        Paragraph("HbA1c", cell_bold),
        Paragraph("6.2", cell_high),
        Paragraph("%", cell_normal),
        Paragraph("4.0 - 5.6", cell_normal),
        Paragraph("HIGH", cell_high),
    ],
]

results_table = Table(test_rows, colWidths=[170, 70, 70, 130, 90])
results_table.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ])
)
story.append(results_table)
story.append(Spacer(1, 25))

# Laboratory Notes / Disclaimer (Non-parsed text to verify graceful degradation)
disclaimer_style = ParagraphStyle(
    "Disclaimer",
    parent=styles["Normal"],
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#64748b"),
)
story.append(Paragraph("<b>CLINICAL NOTES & INTERPRETATION:</b>", disclaimer_style))
story.append(Paragraph(
    "Patient exhibits borderline prediabetic markers (elevated fasting glucose and HbA1c). "
    "Mild microcytic anemia indicated by lower hemoglobin levels. Lipid panel reveals slightly elevated total cholesterol. "
    "Follow-up with primary care physician is recommended within 4 weeks.",
    disclaimer_style,
))
story.append(Spacer(1, 8))
story.append(Paragraph(
    "Electronically signed by: Sarah Jenkins, MD • Verified by Chief Pathologist: Robert Vance, MD • End of Report.",
    disclaimer_style,
))

doc.build(story)
print(f"Sample lab report successfully generated at: {output_pdf_path}")
