"""Smart placeholder detection and preview helpers for imported DOCX templates.

Supports both square-bracket placeholders used by Marathi office documents
(e.g. [प्रतिज्ञाकर्त्याचे पूर्ण नाव]) and brace placeholders
(e.g. {applicant_name}). This module never modifies source documents.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document

# Keep square brackets non-greedy and on one line to avoid swallowing prose.
PLACEHOLDER_PATTERN = re.compile(
    r"\[([^\[\]\r\n]{1,100})\]|\{([^{}\r\n]{1,100})\}"
)

KNOWN_LABELS = {
    "प्रतिज्ञाकर्त्याचे पूर्ण नाव": "प्रतिज्ञाकर्त्याचे पूर्ण नाव",
    "पूर्ण नाव": "पूर्ण नाव",
    "वय": "वय (वर्षे)",
    "व्यवसाय": "व्यवसाय",
    "गाव/पूर्ण पत्ता": "गाव / पूर्ण पत्ता",
    "गाव": "गाव",
    "पूर्ण पत्ता": "पूर्ण पत्ता",
    "पत्ता": "पत्ता",
    "तालुका": "तालुका",
    "जिल्हा": "जिल्हा",
    "गावाचे नाव": "गावाचे नाव",
    "गट क्रमांक/सर्व्हे क्रमांक/घर क्रमांक/प्लॉट क्रमांक": "मालमत्ता क्रमांक",
    "विहीर/शेतजमीन/घर/प्लॉट/इतर मालमत्ता": "मालमत्तेचा प्रकार",
    "शेती/घरगुती/प्लॉटिंग/इतर": "वीज वापराचा उद्देश",
    "कार्यालय/शाखा/तालुका": "महावितरण कार्यालय / शाखा",
    "पहिले नाव": "पहिले नाव",
    "दुसरे नाव": "दुसरे नाव",
    "ठिकाण": "ठिकाण",
    "दिनांक": "दिनांक",
    "applicant_name": "अर्जदाराचे नाव",
    "applicant_full_name": "अर्जदाराचे पूर्ण नाव",
    "applicant_age": "वय (वर्षे)",
    "occupation": "व्यवसाय",
    "address": "पत्ता",
    "village": "गाव",
    "taluka": "तालुका",
    "district": "जिल्हा",
    "date": "दिनांक",
}

def _iter_paragraphs(container):
    """Yield paragraphs from a document/container, including table cells."""
    for paragraph in getattr(container, "paragraphs", []):
        yield paragraph
    for table in getattr(container, "tables", []):
        for row in table.rows:
            for cell in row.cells:
                yield from _iter_paragraphs(cell)

def placeholder_key(match: re.Match[str]) -> str:
    return (match.group(1) or match.group(2) or "").strip()

def extract_docx_fields(docx_path: str | Path) -> list[dict[str, str]]:
    """Return unique placeholder keys in document order with human-friendly labels."""
    doc = Document(str(docx_path))
    fields: list[dict[str, str]] = []
    seen: set[str] = set()
    containers = [doc]
    for section in doc.sections:
        containers.extend([
            section.header, section.footer,
            section.first_page_header, section.first_page_footer,
            section.even_page_header, section.even_page_footer,
        ])
    for container in containers:
        for paragraph in _iter_paragraphs(container):
            for match in PLACEHOLDER_PATTERN.finditer(paragraph.text):
                key = placeholder_key(match)
                if key and key not in seen:
                    seen.add(key)
                    fields.append({"key": key, "label": infer_label(key), "syntax": match.group(0)})
    return fields

def infer_label(key: str) -> str:
    """Infer a readable field label from Marathi placeholder text or snake_case."""
    cleaned = re.sub(r"\s+", " ", key).strip()
    if cleaned in KNOWN_LABELS:
        return KNOWN_LABELS[cleaned]
    # When the placeholder contains slash-separated choices, use the first useful concept.
    if "/" in cleaned:
        parts = [part.strip() for part in cleaned.split("/") if part.strip()]
        if parts:
            first = parts[0]
            if first in KNOWN_LABELS:
                return KNOWN_LABELS[first]
            cleaned = " / ".join(parts[:2])
    cleaned = cleaned.replace("_", " ").strip()
    if re.fullmatch(r"[A-Za-z0-9 ]+", cleaned):
        return cleaned.title()
    return cleaned or "माहिती"

def replace_placeholder_text(text: str, data: dict[str, Any], show_empty: bool = True) -> str:
    """Replace placeholders while preserving unknown or intentionally blank fields."""
    def replacement(match: re.Match[str]) -> str:
        key = placeholder_key(match)
        value = data.get(key, "")
        if value is None:
            value = ""
        value = str(value)
        return value if value.strip() else ("" if not show_empty else match.group(0))
    return PLACEHOLDER_PATTERN.sub(replacement, text)

def build_docx_preview(docx_path: str | Path, data: dict[str, Any]) -> str:
    """Build a readable text preview including paragraphs and tables."""
    doc = Document(str(docx_path))
    lines: list[str] = []
    for paragraph in doc.paragraphs:
        lines.append(replace_placeholder_text(paragraph.text, data))
    for table in doc.tables:
        for row in table.rows:
            lines.append("    ".join(replace_placeholder_text(cell.text, data) for cell in row.cells))
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            text = replace_placeholder_text(paragraph.text, data)
            if text.strip():
                lines.insert(0, text)
        for paragraph in section.footer.paragraphs:
            text = replace_placeholder_text(paragraph.text, data)
            if text.strip():
                lines.append(text)
    return "\n".join(lines).strip()


def detect_docx_font_family(docx_path: str | Path) -> str | None:
    """Return the first useful explicit font family found in document runs.

    Word may inherit fonts from styles, so None means no explicit run font was
    found; callers should then retain their current/default preview font.
    """
    doc = Document(str(docx_path))
    containers = [doc]
    for section in doc.sections:
        containers.extend([
            section.header, section.footer,
            section.first_page_header, section.first_page_footer,
            section.even_page_header, section.even_page_footer,
        ])
    from collections import Counter

    counts: Counter[str] = Counter()
    for container in containers:
        for paragraph in _iter_paragraphs(container):
            for run in paragraph.runs:
                name = (run.font.name or "").strip()
                if name:
                    counts[name] += max(1, len(run.text.strip()))
    if not counts:
        return None
    # Prefer a legacy Marathi font when present, rather than a one-off Latin
    # heading font such as Arial or Calibri.
    legacy = [name for name in counts if any(token in name.casefold() for token in ("dvbw", "ism", "shivaji", "kruti", "kiran"))]
    if legacy:
        return max(legacy, key=lambda name: counts[name])
    return counts.most_common(1)[0][0]
