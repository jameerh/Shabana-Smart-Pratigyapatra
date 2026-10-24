"""Local form-history and validation helpers."""
from __future__ import annotations
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

def append_form_history(history_file, template_name, values):
    """Append a completed-form snapshot for suggestions; never store empty values."""
    path = Path(history_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    if path.exists():
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                records = []
        except (OSError, json.JSONDecodeError):
            records = []
    cleaned = {str(k): str(v).strip() for k, v in values.items() if str(v or "").strip()}
    if not cleaned:
        return path
    record = {"template_name": template_name, "saved_at": datetime.now().isoformat(timespec="seconds"), "values": cleaned}
    records.append(record)
    records = records[-5000:]
    fd, tmp = tempfile.mkstemp(prefix="form_history_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(records, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise
    return path

def history_suggestions(history_file, field_key, limit=20):
    """Return distinct recent values for a field across every template."""
    path = Path(history_file)
    if not path.exists():
        return []
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    result, seen = [], set()
    for record in reversed(records if isinstance(records, list) else []):
        value = str(record.get("values", {}).get(field_key, "")).strip()
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            result.append(value)
            if len(result) >= limit:
                break
    return result

def validate_mobile(value):
    """Accept blank or a 10-digit Indian mobile number (optional +91/91 prefix)."""
    digits = re.sub(r"\D", "", str(value or ""))
    if not digits:
        return True
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return len(digits) == 10 and digits[0] in "6789"

def validate_date(value):
    """Accept common numeric date formats without rejecting blank optional fields."""
    value = str(value or "").strip()
    if not value:
        return True
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            pass
    return False


def clear_form_history(history_file):
    """Delete local applicant form history explicitly requested by the operator."""
    path = Path(history_file)
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise OSError(f"Could not delete form history at {path}: {exc}") from exc
    return not path.exists()
