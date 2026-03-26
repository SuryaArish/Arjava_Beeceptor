"""Services for bulk export and import of Mock APIs."""
import csv
import io
import json
import uuid
from decimal import Decimal
from typing import Any

import pdfplumber
from pydantic import ValidationError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

from app.models import MockApiCreate, FailedRecord


# ── Export ────────────────────────────────────────────────────────────────────

# All fields needed for a round-trip import
_EXPORT_FIELDS = [
    "project_id", "env_id", "method", "description", "is_active",
    "created_by", "updated_by",
    "request_condition", "expression", "state_condition", "query_header", "response",
]


def export_json(items: list[dict]) -> bytes:
    return json.dumps(items, indent=2, default=str).encode()


def export_csv(items: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        row = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in item.items()}
        writer.writerow(row)
    return buf.getvalue().encode()


def export_pdf(items: list[dict], project_id: str) -> bytes:
    """
    Export as PDF. Each row contains all required import fields.
    Dict/list fields are JSON-serialised so they survive text extraction on import.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=15, rightMargin=15,
                            topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Mock APIs — Project: {project_id}", styles["Title"])]

    header = _EXPORT_FIELDS
    rows = [header]
    for item in items:
        row = []
        for f in _EXPORT_FIELDS:
            val = item.get(f, "")
            row.append(json.dumps(val) if isinstance(val, (dict, list)) else str(val))
        rows.append(row)

    col_widths = [60, 60, 40, 80, 40, 60, 60, 80, 80, 80, 80, 80]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2d3748")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTSIZE",      (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.grey),
        ("PADDING",       (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("WORDWRAP",      (0, 0), (-1, -1), True),
    ]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()


# ── Import ────────────────────────────────────────────────────────────────────

def _parse_json_import(content: bytes) -> list[dict]:
    data = json.loads(content)
    return data if isinstance(data, list) else [data]


def _parse_csv_import(content: bytes) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content.decode()))
    rows: list[dict] = []
    for row in reader:
        parsed: dict[str, Any] = {}
        for k, v in row.items():
            try:
                parsed[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                parsed[k] = v
        rows.append(parsed)
    return rows


def _parse_pdf_import(content: bytes) -> list[dict]:
    """
    Extract table rows from a PDF exported by export_pdf().
    The first row is treated as the header; subsequent rows are data.
    Dict/list fields stored as JSON strings are decoded back to objects.
    """
    rows: list[dict] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        header: list[str] | None = None
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for i, row in enumerate(table):
                    # Skip empty rows
                    if not any(cell for cell in row):
                        continue
                    if header is None:
                        # First non-empty row is the header
                        header = [str(cell).strip() for cell in row]
                        continue
                    record: dict[str, Any] = {}
                    for col, cell in zip(header, row):
                        val = str(cell).strip() if cell is not None else ""
                        try:
                            record[col] = json.loads(val)
                        except (json.JSONDecodeError, ValueError):
                            record[col] = val
                    rows.append(record)
    if not rows:
        raise ValueError("No table data found in PDF. Ensure the PDF was exported using the export API.")
    return rows


def parse_import_file(content: bytes, content_type: str, filename: str = "") -> list[dict]:
    """Detect format from content_type or filename and parse into raw dicts."""
    ct = content_type.lower()
    fn = filename.lower()

    if "csv" in ct or fn.endswith(".csv"):
        return _parse_csv_import(content)
    if "pdf" in ct or fn.endswith(".pdf"):
        return _parse_pdf_import(content)
    if "json" in ct or fn.endswith(".json") or "text/plain" in ct:
        return _parse_json_import(content)

    raise ValueError(
        f"Unsupported file type '{content_type}'. Accepted: application/json, text/csv, application/pdf"
    )


def _floats_to_decimal(obj: Any) -> Any:
    """Recursively convert float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _floats_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_floats_to_decimal(v) for v in obj]
    return obj


def validate_and_build_items(
    raw_records: list[dict],
    now: str,
) -> tuple[list[dict], list[FailedRecord]]:
    """Validate each record with MockApiCreate; return (valid_items, failed_records)."""
    valid: list[dict] = []
    failed: list[FailedRecord] = []
    for i, record in enumerate(raw_records):
        try:
            api = MockApiCreate(**record)
            item = _floats_to_decimal(api.model_dump())
            item["api_id"] = str(uuid.uuid4())
            item["created_at"] = now
            item["updated_at"] = now
            valid.append(item)
        except (ValidationError, Exception) as e:
            failed.append(FailedRecord(index=i, reason=str(e), data=record))
    return valid, failed
