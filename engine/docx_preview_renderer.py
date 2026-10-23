"""Optional WYSIWYG DOCX preview using LibreOffice and PyMuPDF.

Requires LibreOffice (soffice.exe) installed locally and PyMuPDF (fitz).
The original DOCX is never modified; rendering uses temporary files.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class PreviewRenderError(RuntimeError):
    pass


def find_office_binary() -> str | None:
    """Find LibreOffice headless executable on common Windows/Linux locations."""
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "LibreOffice/program/soffice.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "LibreOffice/program/soffice.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
    return None


def convert_docx_to_pdf(docx_path: str | Path, output_pdf: str | Path) -> Path:
    """Convert a DOCX to a user-selected PDF path with local LibreOffice."""
    office = find_office_binary()
    if not office:
        raise PreviewRenderError("LibreOffice was not found. Install it to export PDF.")
    source = Path(docx_path).resolve()
    target = Path(output_pdf).resolve()
    if not source.is_file():
        raise PreviewRenderError(f"DOCX not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="shabana_pdf_") as tmp:
        profile = Path(tmp) / "lo_profile"
        command = [
            office, f"-env:UserInstallation={profile.as_uri()}", "--headless",
            "--convert-to", "pdf", "--outdir", str(target.parent), str(source),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
        generated = target.parent / f"{source.stem}.pdf"
        if result.returncode != 0 or not generated.exists():
            detail = (result.stderr or result.stdout or "Unknown LibreOffice error").strip()
            raise PreviewRenderError(f"PDF export failed: {detail}")
        if generated != target:
            if target.exists():
                target.unlink()
            generated.replace(target)
    return target


def render_docx_pages(docx_path: str | Path, dpi: int = 110) -> list[bytes]:
    """Render DOCX to PDF through LibreOffice and return page PNG bytes."""
    office = find_office_binary()
    if not office:
        raise PreviewRenderError(
            "LibreOffice was not found. Install LibreOffice to enable page-accurate preview."
        )
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise PreviewRenderError(
            "PyMuPDF is missing. Run: pip install PyMuPDF"
        ) from exc

    source = Path(docx_path).resolve()
    if not source.is_file():
        raise PreviewRenderError(f"DOCX not found: {source}")
    with tempfile.TemporaryDirectory(prefix="shabana_preview_") as tmp:
        output_dir = Path(tmp)
        profile = output_dir / "lo_profile"
        command = [
            office,
            f"-env:UserInstallation={profile.as_uri()}",
            "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(source),
        ]
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=60, check=False
            )
        except subprocess.TimeoutExpired as exc:
            raise PreviewRenderError("Document rendering timed out after 60 seconds.") from exc
        pdf_path = output_dir / f"{source.stem}.pdf"
        if result.returncode != 0 or not pdf_path.exists():
            detail = (result.stderr or result.stdout or "Unknown LibreOffice error").strip()
            raise PreviewRenderError(f"LibreOffice could not render this DOCX: {detail}")
        pages: list[bytes] = []
        with fitz.open(pdf_path) as pdf:
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            for page in pdf:
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                pages.append(pixmap.tobytes("png"))
        if not pages:
            raise PreviewRenderError("The rendered document contains no pages.")
        return pages
