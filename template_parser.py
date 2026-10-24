"""Placeholder extraction and filling for reusable Word templates."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.shared import Pt

from engine.smart_docx_import import (
    PLACEHOLDER_PATTERN,
    extract_docx_fields,
    replace_placeholder_text,
)


def extract_placeholders(docx_path: str | Path) -> list[str]:
    """Extract unique square-bracket and brace placeholders in document order."""
    return [field["key"] for field in extract_docx_fields(docx_path)]


def _iter_paragraphs(container):
    """Yield paragraphs in the document, including table cells and headers/footers."""
    for paragraph in getattr(container, "paragraphs", []):
        yield paragraph
    for table in getattr(container, "tables", []):
        for row in table.rows:
            for cell in row.cells:
                yield from _iter_paragraphs(cell)


def _replace_paragraph(paragraph, data: dict[str, Any], show_empty: bool = False) -> None:
    """Replace placeholders in a paragraph, retaining its paragraph properties.

    Word can split a placeholder over several runs. Rebuilding only the affected
    paragraph avoids leaving part of a placeholder behind. The first run's
    character formatting is retained; paragraph alignment/spacing remains intact.
    """
    original = paragraph.text
    if not PLACEHOLDER_PATTERN.search(original):
        return
    replacement = replace_placeholder_text(original, data, show_empty=show_empty)
    if replacement == original:
        return

    first_run = paragraph.runs[0] if paragraph.runs else None
    formatting = None
    if first_run is not None:
        font = first_run.font
        formatting = {
            "bold": font.bold,
            "italic": font.italic,
            "underline": font.underline,
            "size": font.size,
            "name": font.name,
            "color": font.color.rgb if font.color and font.color.type is not None else None,
        }
    paragraph.clear()
    run = paragraph.add_run(replacement)
    if formatting:
        run.font.bold = formatting["bold"]
        run.font.italic = formatting["italic"]
        run.font.underline = formatting["underline"]
        run.font.size = formatting["size"]
        run.font.name = formatting["name"]
        if formatting["color"]:
            run.font.color.rgb = formatting["color"]
    else:
        run.font.name = "Mangal"
        run.font.size = Pt(14)


def replace_placeholders(doc, data, show_empty: bool = False):
    """Replace recognized placeholders throughout a DOCX document."""
    containers = [doc]
    for section in doc.sections:
        containers.extend([section.header, section.footer, section.first_page_header,
                           section.first_page_footer, section.even_page_header,
                           section.even_page_footer])
    seen_paragraphs = set()
    for container in containers:
        for paragraph in _iter_paragraphs(container):
            identity = id(paragraph._p)
            if identity in seen_paragraphs:
                continue
            seen_paragraphs.add(identity)
            _replace_paragraph(paragraph, data, show_empty=show_empty)
    return doc


def create_filled_document(template_path, data, output_path, show_empty: bool = False):
    """Load a template, replace placeholders, and save the completed document."""
    doc = Document(str(template_path))
    replace_placeholders(doc, data, show_empty=show_empty)
    doc.save(str(output_path))
    return str(output_path)
