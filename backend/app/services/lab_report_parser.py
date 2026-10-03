import io
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Common unit patterns in lab diagnostics
UNIT_PATTERN = r"(?:g/dL|g/dl|mg/dL|mg/dl|mmol/L|umol/L|µmol/L|uIU/mL|µIU/mL|mIU/L|mIU/mL|ng/mL|pg/mL|mEq/L|IU/L|U/L|cells/mcL|/cumm|10\^3/uL|10\*3/uL|10\^6/uL|%|sec|seconds|mm/hr|fL|fl|pg)"

# Range patterns:
# 1. min - max e.g. "13.5 - 17.5" or "13.5-17.5" or "70 to 99"
# 2. < max e.g. "< 200", "<= 100", "up to 5.0"
# 3. > min e.g. "> 40", ">= 60"
RANGE_HYPHEN_RE = re.compile(
    r"(?P<low>\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(?P<high>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
RANGE_LESS_RE = re.compile(
    r"(?:<|<=|less\s+than|up\s+to)\s*(?P<high>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
RANGE_GREATER_RE = re.compile(
    r"(?:>|>=|greater\s+than)\s*(?P<low>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _cluster_ocr_results_into_lines(result) -> str:
    """
    Takes RapidOCR result items [(box, text, score), ...],
    clusters them into horizontal lines using Y-coordinates,
    and sorts words left-to-right to reconstruct tabular prescription text accurately.
    """
    if not result:
        return ""
    raw_boxes = []
    for box, text, score in result:
        if not text or not text.strip():
            continue
        y_center = (box[0][1] + box[2][1]) / 2.0
        x_min = min(p[0] for p in box)
        raw_boxes.append({"y": y_center, "x": x_min, "text": text.strip()})

    raw_boxes.sort(key=lambda b: b["y"])
    rows = []
    for b in raw_boxes:
        placed = False
        for r in rows:
            avg_y = sum(item["y"] for item in r) / len(r)
            if abs(b["y"] - avg_y) <= 14:
                r.append(b)
                placed = True
                break
        if not placed:
            rows.append([b])

    reconstructed_lines = []
    for r in rows:
        r.sort(key=lambda b: b["x"])
        reconstructed_lines.append(" ".join(item["text"] for item in r))

    return "\n".join(reconstructed_lines)


def extract_text_from_pdf_or_image(
    file_bytes: bytes,
    filename: str,
) -> str:
    """
    Extracts text from PDF or image bytes.
    First tries native text extraction for PDFs.
    If native text is empty/minimal or the file is an image, attempts OCR.
    Handles missing host dependencies gracefully without crashing.
    """
    lower_name = filename.lower()
    is_pdf = lower_name.endswith(".pdf")
    extracted_text = ""

    if is_pdf:
        # Step 1: Native PDF text extraction using pdfplumber
        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt:
                        pages_text.append(txt)
                extracted_text = "\n".join(pages_text).strip()
        except Exception as e:
            logger.warning("pdfplumber native extraction encountered an issue: %s", e)

        # Fallback to pypdf if pdfplumber extracted nothing
        if not extracted_text:
            try:
                import pypdf

                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages_text = []
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt:
                        pages_text.append(txt)
                extracted_text = "\n".join(pages_text).strip()
            except Exception as e:
                logger.warning("pypdf extraction encountered an issue: %s", e)

        # If native PDF text is substantial (> 40 chars), we don't need OCR
        if len(extracted_text) >= 40:
            logger.info("Successfully extracted %d characters from native PDF.", len(extracted_text))
            return extracted_text

        logger.info("PDF has minimal native text (%d chars). Attempting OCR fallback...", len(extracted_text))

    # Step 2: OCR Fallback (for scanned PDF or images)
    try:
        from PIL import Image
        import numpy as np

        # Primary OCR: RapidOCR (cross-platform ONNX runtime, no external binary needed)
        try:
            from rapidocr_onnxruntime import RapidOCR

            engine = RapidOCR()
            if is_pdf:
                try:
                    import pypdfium2

                    pdf_doc = pypdfium2.PdfDocument(file_bytes)
                    ocr_parts = []
                    for page_idx in range(min(3, len(pdf_doc))):
                        page = pdf_doc[page_idx]
                        pil_img = page.render(scale=2.0).to_pil()
                        res, _ = engine(np.array(pil_img))
                        clustered = _cluster_ocr_results_into_lines(res)
                        if clustered:
                            ocr_parts.append(clustered)
                    if ocr_parts:
                        return "\n".join(ocr_parts).strip()
                except Exception as e:
                    logger.warning("pypdfium2/RapidOCR on PDF failed: %s", e)
            else:
                img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                res, _ = engine(np.array(img))
                clustered = _cluster_ocr_results_into_lines(res)
                if clustered:
                    return clustered.strip()
        except ImportError:
            logger.info("rapidocr_onnxruntime not installed, checking pytesseract fallback.")

        # Secondary OCR Fallback: pytesseract
        import pytesseract

        if is_pdf:
            try:
                from pdf2image import convert_from_bytes

                images = convert_from_bytes(file_bytes, first_page=1, last_page=3)
                ocr_text_parts = []
                for img in images:
                    ocr_text_parts.append(pytesseract.image_to_string(img))
                ocr_text = "\n".join(ocr_text_parts).strip()
                if ocr_text:
                    return ocr_text
            except Exception as e:
                logger.warning(
                    "pdf2image/pytesseract OCR on PDF failed: %s",
                    e,
                )
        else:
            # Image files (.png, .jpg, .jpeg, etc.)
            try:
                img = Image.open(io.BytesIO(file_bytes))
                ocr_text = pytesseract.image_to_string(img).strip()
                if ocr_text:
                    return ocr_text
            except Exception as e:
                logger.warning(
                    "pytesseract OCR on image failed: %s",
                    e,
                )
    except ImportError as e:
        logger.warning("OCR libraries not available: %s", e)

    # Return whatever text we managed to extract (or empty string)
    return extracted_text


def parse_reference_range(range_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parses strings like '13.5 - 17.5', '< 200', '> 40', '0.7-1.3' into (low, high).
    """
    cleaned = range_str.strip()

    # Case 1: hyphenated range: "13.5 - 17.5"
    m_hyphen = RANGE_HYPHEN_RE.search(cleaned)
    if m_hyphen:
        try:
            low = float(m_hyphen.group("low"))
            high = float(m_hyphen.group("high"))
            return low, high
        except ValueError:
            pass

    # Case 2: "< 200" or "<= 100"
    m_less = RANGE_LESS_RE.search(cleaned)
    if m_less:
        try:
            high = float(m_less.group("high"))
            return None, high
        except ValueError:
            pass

    # Case 3: "> 40" or ">= 60"
    m_greater = RANGE_GREATER_RE.search(cleaned)
    if m_greater:
        try:
            low = float(m_greater.group("low"))
            return low, None
        except ValueError:
            pass

    return None, None


def classify_flag(
    value: float,
    ref_low: Optional[float],
    ref_high: Optional[float],
) -> str:
    """
    Classifies a test value as 'normal', 'high', 'low', or 'unknown'.
    """
    if ref_low is not None and ref_high is not None:
        if value < ref_low:
            return "low"
        elif value > ref_high:
            return "high"
        else:
            return "normal"
    elif ref_low is not None:
        if value < ref_low:
            return "low"
        else:
            return "normal"
    elif ref_high is not None:
        if value > ref_high:
            return "high"
        else:
            return "normal"

    return "unknown"


def parse_lab_report_text(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses structured test entries from raw text line by line.
    Logs unparseable lines rather than crashing.
    Returns list of dicts with keys:
    - test_name: str
    - value: float
    - unit: str
    - reference_low: Optional[float]
    - reference_high: Optional[float]
    - flag: str
    """
    if not raw_text:
        return []

    lines = raw_text.splitlines()
    structured_entries = []

    # Regex to match:
    # <test name> <value> [optional flag word like High/Low] <unit> <ref_range>
    # Supports pipe (|) or colon (:) or whitespace delimiters
    # Example matches:
    # "Hemoglobin 11.2 g/dL 13.5-17.5"
    # "Fasting Blood Glucose | 115.0 | mg/dL | 70 - 99"
    # "Total Cholesterol 220 mg/dL < 200"
    # "HDL Cholesterol 35 mg/dL > 40"
    pattern = re.compile(
        rf"^(?P<test>[A-Za-z0-9\s\(\)\-\/\,\.\+]+?)"          # Test Name
        rf"(?:\s*[:\|\t]\s*|\s+)"                             # Separator
        rf"(?P<val>\d+(?:\.\d+)?)"                            # Result Value
        rf"(?:\s*(?:high|low|normal|h|l|n)\b)?"               # Optional inline status flag
        rf"\s+(?P<unit>{UNIT_PATTERN}|[A-Za-z%/\^\*\d]+)"     # Unit
        rf"(?:\s*[:\|\t]\s*|\s+)"                             # Separator
        rf"(?P<range>(?:<|>|<=|>=|less\s+than|up\s+to|greater\s+than)?\s*\d+(?:\.\d+)?(?:\s*(?:-|–|—|to)\s*\d+(?:\.\d+)?)?)" # Ref Range
        rf".*$",
        re.IGNORECASE,
    )

    # Secondary pattern for lines where unit might follow value directly or slightly different spacing:
    # e.g., "Hemoglobin : 14.5 g/dL (13.0 - 17.0)"
    alt_pattern = re.compile(
        rf"^(?P<test>[A-Za-z0-9\s\(\)\-\/\,\.\+]+?)"
        rf"(?:\s*[:\|\t]\s*|\s+)"
        rf"(?P<val>\d+(?:\.\d+)?)\s*"
        rf"(?P<unit>{UNIT_PATTERN})?"
        rf"\s*(?:[\(\[])?"
        rf"(?P<range>(?:<|>|<=|>=)?\s*\d+(?:\.\d+)?\s*(?:-|–|—|to)\s*\d+(?:\.\d+)?|<=\s*\d+(?:\.\d+)?|>=\s*\d+(?:\.\d+)?|<\s*\d+(?:\.\d+)?|>\s*\d+(?:\.\d+)?)"
        rf"(?:[\)\]])?",
        re.IGNORECASE,
    )

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Skip obvious document header/metadata lines
        lower_line = line.lower()
        if any(h in lower_line for h in [
            "patient name", "date of report", "doctor:", "dr.", "sample collected",
            "page ", "lab report", "test name", "reference range", "bio-reference",
            "diagnostic center", "hospital", "pathology", "consultant"
        ]):
            logger.debug("Skipping header/metadata line: %s", line)
            continue

        match = pattern.match(line)
        if not match:
            match = alt_pattern.match(line)

        if match:
            test_name = match.group("test").strip(" :|-,\t")
            val_str = match.group("val").strip()
            unit_str = (match.group("unit") or "").strip(" :|-,\t")
            range_str = (match.group("range") or "").strip(" :|-,\t()[]")

            # Validate test name is reasonable (not just numbers or short punctuation)
            if len(test_name) < 2 or re.match(r"^\d+$", test_name):
                logger.info("Unparsed report line (invalid test name): %s", line)
                continue

            try:
                val = float(val_str)
            except ValueError:
                logger.info("Unparsed report line (failed float conversion): %s", line)
                continue

            ref_low, ref_high = parse_reference_range(range_str)
            flag = classify_flag(val, ref_low, ref_high)

            structured_entries.append({
                "test_name": test_name,
                "value": val,
                "unit": unit_str or "units",
                "reference_low": ref_low,
                "reference_high": ref_high,
                "flag": flag,
            })
        else:
            # Graceful degradation: Log unparsed line without failing
            logger.info("Unparsed report line: %s", line)

    return structured_entries
