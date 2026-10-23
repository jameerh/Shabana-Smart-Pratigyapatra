"""Mine reusable DOCX templates from legacy documents with bold-filled values.

The miner is deliberately conservative: bold runs are candidates, not proof of
customer data. It emits a reviewable report and never overwrites the source file.
Requires python-docx (already used by this project).
"""
from __future__ import annotations

import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph


FIELD_RULES = (
    (re.compile(r"(?:नाव|नांव|name|applicant|अर्जदार|मी)\s*[:：]?\s*$", re.I), "applicant_name", "अर्जदाराचे नाव"),
    (re.compile(r"(?:वय|age)\s*[:：]?\s*$", re.I), "applicant_age", "वय"),
    (re.compile(r"(?:व्यवसाय|occupation|धंदा)\s*[:：]?\s*$", re.I), "occupation", "व्यवसाय"),
    (re.compile(r"(?:आधार|aadhaar|aadhar)\s*(?:क्रमांक|नंबर|no\.?|number)?\s*[:：]?\s*$", re.I), "aadhaar_number", "आधार क्रमांक"),
    (re.compile(r"(?:पॅन|pan)\s*(?:क्रमांक|no\.?|number)?\s*[:：]?\s*$", re.I), "pan_number", "पॅन क्रमांक"),
    (re.compile(r"(?:पत्ता|address|रा\.?|राहणार)\s*[:：]?\s*$", re.I), "address", "पत्ता"),
    (re.compile(r"(?:गाव|मौजे|village)\s*[:：]?\s*$", re.I), "village", "गाव"),
    (re.compile(r"(?:तालुका|taluka|tehsil)\s*[:：]?\s*$", re.I), "taluka", "तालुका"),
    (re.compile(r"(?:जिल्हा|district)\s*[:：]?\s*$", re.I), "district", "जिल्हा"),
    (re.compile(r"(?:दिनांक|तारीख|date)\s*[:：]?\s*$", re.I), "date", "दिनांक"),
    (re.compile(r"(?:सर्वे|गट)\s*(?:क्रमांक|नंबर|क्र\.?|no\.?)?\s*[:：]?\s*$", re.I), "survey_number", "सर्वे / गट क्रमांक"),
    (re.compile(r"(?:क्षेत्र|area)\s*[:：]?\s*$", re.I), "area", "क्षेत्र"),
    (re.compile(r"(?:रक्कम|उत्पन्न|income|amount)\s*[:：]?\s*$", re.I), "amount", "रक्कम / उत्पन्न"),
)

@dataclass(frozen=True)
class FieldCandidate:
    name: str
    label: str
    value: str
    confidence: float
    context: str
    location: str

@dataclass
class MiningResult:
    source_path: str
    output_path: Optional[str]
    fields: list[FieldCandidate]
    paragraphs_scanned: int
    tables_scanned: int
    warnings: list[str]

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "fields": [asdict(field) for field in self.fields],
            "paragraphs_scanned": self.paragraphs_scanned,
            "tables_scanned": self.tables_scanned,
            "warnings": self.warnings,
        }


def _iter_block_items(parent) -> Iterator[Paragraph | Table]:
    """Yield paragraphs and tables in document order, including table cells."""
    if isinstance(parent, DocumentObject):
        parent_element = parent.element.body
    elif isinstance(parent, _Cell):
        parent_element = parent._tc
    else:
        parent_element = parent
    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _iter_paragraphs(parent) -> Iterator[tuple[Paragraph, str]]:
    for block_index, block in enumerate(_iter_block_items(parent), 1):
        if isinstance(block, Paragraph):
            yield block, f"paragraph:{block_index}"
        else:
            for row_index, row in enumerate(block.rows, 1):
                for cell_index, cell in enumerate(row.cells, 1):
                    for para_index, paragraph in enumerate(cell.paragraphs, 1):
                        yield paragraph, f"table:{block_index}/row:{row_index}/cell:{cell_index}/paragraph:{para_index}"
                    for nested_index, nested in enumerate(cell.tables, 1):
                        yield from _iter_paragraphs(nested)


def _run_is_bold(run) -> bool:
    """Resolve direct formatting and paragraph style; unknown means not bold."""
    if run.bold is not None:
        return bool(run.bold)
    try:
        return bool(run.style and run.style.font.bold)
    except (AttributeError, TypeError):
        return False


def _slug(value: str) -> str:
    value = re.sub(r"[^\w]+", "_", value.strip().lower(), flags=re.UNICODE).strip("_")
    return value or "value"


def _infer_field(context: str, index: int) -> tuple[str, str, float]:
    compact = re.sub(r"\s+", " ", context).strip()
    for pattern, name, label in FIELD_RULES:
        if pattern.search(compact[-100:]):
            return name, label, 0.92
    # A short trailing label often gives better context than the whole clause.
    tail = compact[-45:].strip(" :：,，;；.-")
    if tail and len(tail) <= 24 and not re.search(r"[.!?।]", tail):
        return f"field_{index}_{_slug(tail)}", tail, 0.58
    return f"field_{index}", f"Field {index}", 0.35


def _paragraph_bold_groups(paragraph: Paragraph) -> list[tuple[list[int], str, str]]:
    """Return (run_indices, value, preceding-context) for adjacent bold runs."""
    groups: list[tuple[list[int], str, str]] = []
    runs = paragraph.runs
    current_indices: list[int] = []
    current_text = ""
    for index, run in enumerate(runs):
        if _run_is_bold(run) and run.text:
            current_indices.append(index)
            current_text += run.text
        else:
            if current_indices:
                groups.append((current_indices, current_text, ""))
                current_indices, current_text = [], ""
    if current_indices:
        groups.append((current_indices, current_text, ""))

    enriched = []
    for run_indices, value, _ in groups:
        start_index = run_indices[0]
        context = "".join(run.text for run in runs[:start_index] if not _run_is_bold(run))
        enriched.append((run_indices, value, context))
    return enriched


def mine_docx(source_path: str | Path, output_path: str | Path | None = None) -> MiningResult:
    """Mine bold values and optionally save a placeholder-template DOCX.

    Source is never changed. Generated placeholders retain the formatting of the
    first bold run in each candidate group. Low-confidence fields are still
    surfaced for operator review rather than silently treated as certain.
    """
    source = Path(source_path)
    if source.suffix.lower() != ".docx":
        raise ValueError(f"Expected a .docx file, got: {source.name}")
    if not source.is_file():
        raise FileNotFoundError(source)

    document = Document(str(source))
    output_document = Document(str(source)) if output_path else None
    fields: list[FieldCandidate] = []
    warnings: list[str] = []
    paragraph_count = 0
    table_count = 0
    field_index = 0

    # Align source and output paragraphs in document order; both documents were
    # loaded from the same file, so their traversal shapes are identical.
    source_paragraphs = list(_iter_paragraphs(document))
    output_paragraphs = list(_iter_paragraphs(output_document)) if output_document else []
    for paragraph_index, (paragraph, location) in enumerate(source_paragraphs):
        paragraph_count += 1
        if location.startswith("table:"):
            table_count += 1
        groups = _paragraph_bold_groups(paragraph)
        if not groups:
            continue
        output_paragraph = output_paragraphs[paragraph_index][0] if output_document else None
        for group_run_indices, value, context in groups:
            value = value.strip()
            if not value:
                continue
            field_index += 1
            name, label, confidence = _infer_field(context, field_index)
            # Repeated inferred names need stable unique keys within one document.
            existing = {field.name for field in fields}
            if name in existing:
                name = f"{name}_{sum(1 for field in fields if field.name.startswith(name)) + 1}"
            fields.append(FieldCandidate(name, label, value, confidence, context.strip(), location))

            if output_paragraph is not None:
                # Find corresponding run positions by index rather than relying on
                # run object identity across independently parsed DOCX instances.
                source_run_indices = group_run_indices
                if source_run_indices:
                    output_runs = output_paragraph.runs
                    first_index = source_run_indices[0]
                    if first_index < len(output_runs):
                        output_runs[first_index].text = "{" + name + "}"
                        for run_index in source_run_indices[1:]:
                            if run_index < len(output_runs):
                                output_runs[run_index].text = ""

    if not fields:
        warnings.append("No bold text candidates were found. Check that customer values use direct bold formatting or a bold paragraph style.")
    if output_document is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        output_document.save(str(destination))
        output_value: Optional[str] = str(destination)
    else:
        output_value = None

    return MiningResult(str(source), output_value, fields, paragraph_count, table_count, warnings)


def mine_folder(folder_path: str | Path, output_folder: str | Path) -> list[MiningResult]:
    """Mine every DOCX in a folder into a separate output folder.

    Temporary Office lock files (``~$*.docx``) and the output folder itself are
    excluded. Deduplication is intentionally a separate pass/module.
    """
    folder = Path(folder_path).resolve()
    output = Path(output_folder).resolve()
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    if folder == output or folder in output.parents:
        # Output may be nested inside input, but it must be excluded below.
        pass
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for source in sorted(folder.rglob("*.docx")):
        if source.name.startswith("~$") or output == source.parent or output in source.parents:
            continue
        destination = output / f"{source.stem}.template.docx"
        results.append(mine_docx(source, destination))
    return results
