"""Batch template mining pipeline that combines bold mining, inter-file deduplication,
and repeated section compression into a single structured operation.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from engine.bold_template_miner import mine_docx, MiningResult
from engine.template_deduplicator import (
    Fingerprint,
    DuplicateMatch,
    fingerprint_docx,
    classify_duplicate,
)
from engine.section_repeater import detect_repeated_person_sections


@dataclass
class BulkBatchReport:
    total_scanned: int
    unique_mined: int
    duplicates_skipped: int
    repeated_sections_compressed: int
    templates: List[Dict[str, Any]]
    skipped_files: List[Dict[str, Any]]


def process_template_folder(
    input_folder: str | Path,
    output_folder: str | Path,
    similarity_threshold: float = 0.95
) -> BulkBatchReport:
    """Process all DOCX in input_folder, skip duplicates, compress repeats, and save templates."""
    input_path = Path(input_folder).resolve()
    output_path = Path(output_folder).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    docx_files = [p for p in sorted(input_path.rglob("*.docx"))
                  if not p.name.startswith("~$") and output_path != p.parent and output_path not in p.parents]

    unique_fps: List[Fingerprint] = []
    mined_templates: List[Dict[str, Any]] = []
    skipped_list: List[Dict[str, Any]] = []
    repeated_compressed_count = 0

    for doc_path in docx_files:
        # Check repeated sections inside the document
        repeat_info = detect_repeated_person_sections(doc_path)
        if repeat_info.is_repeated:
            repeated_compressed_count += 1

        # Check inter-file deduplication
        candidate_fp = fingerprint_docx(doc_path)
        dup = classify_duplicate(candidate_fp, unique_fps, threshold=similarity_threshold)
        if dup is not None:
            skipped_list.append({
                "file": doc_path.name,
                "matched_with": Path(dup.matched_path).name,
                "similarity": round(dup.similarity * 100, 1),
                "reason": dup.decision
            })
            continue

        # Mine bold values
        dest_template = output_path / f"{doc_path.stem}.template.docx"
        mining_result = mine_docx(doc_path, dest_template)
        unique_fps.append(candidate_fp)

        mined_templates.append({
            "name": doc_path.stem.replace("_", " ").title(),
            "source": str(doc_path),
            "template_docx": str(dest_template),
            "field_count": len(mining_result.fields),
            "fields": [f.name for f in mining_result.fields],
            "field_details": [asdict(f) for f in mining_result.fields],
            "is_multi_person_repeated": repeat_info.is_repeated,
            "segment_count": repeat_info.segment_count,
        })

    report = BulkBatchReport(
        total_scanned=len(docx_files),
        unique_mined=len(mined_templates),
        duplicates_skipped=len(skipped_list),
        repeated_sections_compressed=repeated_compressed_count,
        templates=mined_templates,
        skipped_files=skipped_list
    )

    # Save summary report JSON in output folder
    report_file = output_path / "mining_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    return report
