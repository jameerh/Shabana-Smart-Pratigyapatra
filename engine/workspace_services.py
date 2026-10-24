"""Local-first workspace services for profiles, template history and document checks.

All data remains on the user's computer. Writes use atomic replacement to reduce
corruption risk. These helpers intentionally avoid network/cloud dependencies.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _atomic_json(path: str | Path, payload: Any) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return target


def save_applicant_profile(directory: str | Path, name: str, values: dict[str, Any]) -> Path:
    """Save a reusable applicant profile as a local JSON file."""
    clean_name = re.sub(r"[^\w.-]+", "_", name.strip(), flags=re.UNICODE).strip("._")
    if not clean_name:
        raise ValueError("Profile name cannot be empty.")
    payload = {
        "schema_version": 1,
        "profile_name": name.strip(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "values": {str(k): str(v) for k, v in values.items()},
    }
    return _atomic_json(Path(directory) / f"{clean_name}.json", payload)


def load_applicant_profile(path: str | Path) -> dict[str, str]:
    """Load and validate a local applicant profile."""
    with Path(path).open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload.get("schema_version") != 1 or not isinstance(payload.get("values"), dict):
        raise ValueError("Unsupported or invalid applicant profile file.")
    return {str(k): str(v) for k, v in payload["values"].items()}


def snapshot_template(source_path: str | Path, history_dir: str | Path, template_name: str) -> Path:
    """Archive a content-addressed copy of a template with metadata."""
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    safe = re.sub(r"[^\w.-]+", "_", template_name.strip(), flags=re.UNICODE).strip("._") or "template"
    folder = Path(history_dir) / safe
    folder.mkdir(parents=True, exist_ok=True)
    snapshot = folder / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{digest[:12]}{source.suffix.lower()}"
    if not snapshot.exists():
        snapshot.write_bytes(raw)
    _atomic_json(snapshot.with_suffix(snapshot.suffix + ".json"), {
        "schema_version": 1,
        "template_name": template_name,
        "source_filename": source.name,
        "sha256": digest,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return snapshot


def list_template_snapshots(history_dir: str | Path, template_name: str) -> list[Path]:
    safe = re.sub(r"[^\w.-]+", "_", template_name.strip(), flags=re.UNICODE).strip("._") or "template"
    folder = Path(history_dir) / safe
    if not folder.exists():
        return []
    return sorted((p for p in folder.iterdir() if p.suffix.lower() == ".docx"), reverse=True)


def validate_required_fields(values: dict[str, Any], required: list[str]) -> list[str]:
    """Return required field keys that are missing or whitespace-only."""
    return [key for key in required if not str(values.get(key, "") or "").strip()]


def compare_text_documents(original: str, generated: str) -> dict[str, Any]:
    """Return a human-readable line diff and simple similarity score."""
    left = original.splitlines()
    right = generated.splitlines()
    matcher = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
    return {
        "similarity_percent": round(matcher.ratio() * 100, 2),
        "added_lines": [line for line in difflib.ndiff(left, right) if line.startswith("+ ")],
        "removed_lines": [line for line in difflib.ndiff(left, right) if line.startswith("- ")],
        "unified_diff": "\n".join(difflib.unified_diff(left, right, fromfile="original", tofile="generated", lineterm="")),
    }


def export_profile_settings(path: str | Path, settings: dict[str, Any]) -> Path:
    """Save export preferences such as font family, page size and margins."""
    return _atomic_json(path, {"schema_version": 1, "settings": settings})


def load_profile_settings(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload.get("schema_version") != 1 or not isinstance(payload.get("settings"), dict):
        raise ValueError("Unsupported or invalid export settings.")
    return payload["settings"]
