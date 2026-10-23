"""Multi-person intra-document repeating section extractor.

Detects when an affidavit has repeating sections for multiple people
(e.g., Person 1 on Page 1 / Section 1, Person 2 on Section 2, Person 3 on Section 3)
and collapses the structure into a single loopable template with record list.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple

from docx import Document

from engine.template_deduplicator import normalize_skeleton, compare_fingerprints, Fingerprint


@dataclass
class RepeatedSectionResult:
    is_repeated: bool
    segment_count: int
    master_template_text: str
    record_fields: List[str]
    extracted_records: List[Dict[str, str]]
    confidence: float


DELIMITER_PATTERNS = [
    re.compile(r"^(?:पृष्ठ|page|व्यक्ती|अर्जदार|वारस)\s*(?:क्रमांक|नं\.?|no\.?)?\s*\d+", re.I),
    re.compile(r"^प्रतिज्ञापत्र\s*$", re.I),
]


def detect_repeated_person_sections(docx_path: str | Path, min_similarity: float = 0.85) -> RepeatedSectionResult:
    """Analyze paragraphs in a document to detect repeating sections for different people.

    Identifies repeated headers (like 'प्रतिज्ञापत्र', 'पृष्ठ १/२', 'व्यक्ती १/२')
    or explicit block repetitions.
    """
    doc = Document(str(docx_path))
    raw_paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    if not raw_paras:
        return RepeatedSectionResult(
            is_repeated=False, segment_count=0, master_template_text="",
            record_fields=[], extracted_records=[], confidence=0.0
        )

    # 1. First, check if a specific pattern repeats multiple times (e.g., exact matches of 'प्रतिज्ञापत्र')
    split_indices = []
    for pattern in DELIMITER_PATTERNS:
        matches = [idx for idx, t in enumerate(raw_paras) if pattern.search(t)]
        if len(matches) >= 2:
            split_indices = matches
            break

    # 2. Fallback: Check if first paragraph of doc repeats later in the text
    if len(split_indices) < 2 and len(raw_paras) >= 4:
        first_line = raw_paras[0]
        if len(first_line) <= 50:
            first_matches = [idx for idx, t in enumerate(raw_paras) if t == first_line]
            if len(first_matches) >= 2:
                split_indices = first_matches

    # If no delimiter splits were found, check if it's a single record
    if len(split_indices) < 2:
        return RepeatedSectionResult(
            is_repeated=False,
            segment_count=1,
            master_template_text="\n\n".join(raw_paras),
            record_fields=[],
            extracted_records=[],
            confidence=1.0
        )

    # Ensure index 0 is start if first delimiter was at 0
    if split_indices[0] != 0:
        split_indices.insert(0, 0)

    # Slice segments
    segments_text = []
    for i in range(len(split_indices)):
        start = split_indices[i]
        end = split_indices[i+1] if i + 1 < len(split_indices) else len(raw_paras)
        seg_text = "\n".join(raw_paras[start:end])
        if seg_text.strip():
            segments_text.append(seg_text)

    if len(segments_text) < 2:
        return RepeatedSectionResult(
            is_repeated=False,
            segment_count=1,
            master_template_text="\n\n".join(raw_paras),
            record_fields=[],
            extracted_records=[],
            confidence=1.0
        )

    # Compare skeleton of segment 0 and segment 1
    skel0 = normalize_skeleton(segments_text[0])
    skel1 = normalize_skeleton(segments_text[1])
    sim = compare_fingerprints(Fingerprint("", "", skel0, len(skel0)),
                               Fingerprint("", "", skel1, len(skel1)))

    if sim >= min_similarity:
        return RepeatedSectionResult(
            is_repeated=True,
            segment_count=len(segments_text),
            master_template_text=segments_text[0],
            record_fields=["applicant_name", "applicant_age", "relation"],
            extracted_records=[],
            confidence=sim
        )

    return RepeatedSectionResult(
        is_repeated=False,
        segment_count=1,
        master_template_text="\n\n".join(raw_paras),
        record_fields=[],
        extracted_records=[],
        confidence=1.0
    )
