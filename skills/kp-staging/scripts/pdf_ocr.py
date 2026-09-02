"""Local OCR support shared by the PDF preprocessors.

OCR derivatives are disposable cache files.  They must never replace a source
PDF: their name is derived from the source bytes and the OCR configuration.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OCR_CACHE_DIR = ".kp-cache/ocr"
DEFAULT_OCR_LANGUAGE = "eng"
OCRMY_PDF_OPTIONS = ("--skip-text", "--deskew", "--rotate-pages")


class OcrDependencyError(RuntimeError):
    """OCRmyPDF or one of its local prerequisites is unavailable."""


class OcrProcessingError(RuntimeError):
    """OCRmyPDF could not create a usable derivative."""


@dataclass(frozen=True)
class OcrSettings:
    mode: str = "auto"
    languages: tuple[str, ...] = (DEFAULT_OCR_LANGUAGE,)
    cache_dir: Path = Path(DEFAULT_OCR_CACHE_DIR)

    @classmethod
    def from_args(cls, mode: str, language: str, cache_dir: str) -> "OcrSettings":
        if mode not in {"auto", "off", "force"}:
            raise ValueError("--ocr must be one of: auto, off, force")
        languages = normalize_languages(language)
        return cls(mode=mode, languages=languages, cache_dir=Path(cache_dir))


def normalize_languages(value: str) -> tuple[str, ...]:
    """Accept Tesseract's `eng+fra` and a friendlier comma-separated form."""
    languages = tuple(part.strip() for part in value.replace(",", "+").split("+") if part.strip())
    if not languages:
        raise ValueError("--ocr-language must name at least one Tesseract language")
    if any(not language.replace("_", "").isalnum() for language in languages):
        raise ValueError("--ocr-language may contain only Tesseract language codes")
    return languages


def source_sha256(source_file: Path) -> str:
    digest = hashlib.sha256()
    with source_file.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_path(source_file: Path, settings: OcrSettings) -> tuple[Path, str]:
    source_hash = source_sha256(source_file)
    config = "|".join((*OCRMY_PDF_OPTIONS, "+".join(settings.languages)))
    config_hash = hashlib.sha256(config.encode()).hexdigest()[:12]
    languages = "+".join(settings.languages)
    return settings.cache_dir / f"{source_hash}-{languages}-{config_hash}.pdf", source_hash


def existing_derivative(source_file: Path, settings: OcrSettings) -> tuple[Path, str] | None:
    path, digest = cache_path(source_file, settings)
    return (path, digest) if path.is_file() else None


def _installation_guidance(missing: list[str], languages: tuple[str, ...]) -> str:
    packages = ["ocrmypdf", *(f"tesseract-ocr-{language}" for language in languages)]
    return (
        f"Missing local OCR prerequisite(s): {', '.join(missing)}. "
        "Install OCRmyPDF, Tesseract, Ghostscript, and the requested Tesseract language data. "
        f"On Ubuntu/Debian: sudo apt install {' '.join(packages)} ghostscript. "
        "For a Python-managed OCRmyPDF, run `uv tool install ocrmypdf` only after installing "
        "the system packages. Re-run with `--ocr off` to retain the original AnyDoc-only behavior."
    )


def check_dependencies(languages: tuple[str, ...]) -> None:
    missing = [name for name in ("ocrmypdf", "tesseract", "gs") if shutil.which(name) is None]
    if missing:
        raise OcrDependencyError(_installation_guidance(missing, languages))

    completed = subprocess.run(
        ["tesseract", "--list-langs"], capture_output=True, text=True, check=False
    )
    installed = set(completed.stdout.splitlines()) if completed.returncode == 0 else set()
    unavailable = [language for language in languages if language not in installed]
    if unavailable:
        names = [f"Tesseract language data ({language})" for language in unavailable]
        raise OcrDependencyError(_installation_guidance(names, languages))


def create_derivative(source_file: Path, settings: OcrSettings) -> tuple[Path, str, bool]:
    """Return `(path, source_hash, created)` without ever modifying the source."""
    derivative, digest = cache_path(source_file, settings)
    if derivative.is_file():
        return derivative, digest, False

    check_dependencies(settings.languages)
    derivative.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ocrmypdf", *OCRMY_PDF_OPTIONS, "--language", "+".join(settings.languages),
        str(source_file), str(derivative),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0 or not derivative.is_file():
        diagnostic = (completed.stderr or completed.stdout or "no diagnostic was returned").strip()
        raise OcrProcessingError(
            "OCRmyPDF failed to create a local OCR derivative "
            f"(exit {completed.returncode}): {diagnostic}"
        )
    return derivative, digest, True


def metadata(cache_file: Path, source_hash: str, settings: OcrSettings) -> dict[str, object]:
    return {
        "ocr_applied": True,
        "ocr_engine": "ocrmypdf",
        "ocr_languages": list(settings.languages),
        "ocr_cache_path": str(cache_file),
        "ocr_source_hash": f"sha256:{source_hash}",
    }


def ocr_required(error: BaseException) -> bool:
    """Recognize OCR-specific converter failures while retaining a safe fallback.

    AnyDoc currently exposes OCR failures as ConvertError text rather than a
    public typed exception.  Prefer error attributes if a later version adds
    them, then use the narrowly-scoped OCR terms as compatibility fallback.
    """
    for name in ("code", "kind", "reason", "error_code"):
        value = getattr(error, name, None)
        if isinstance(value, str) and value.lower() in {"ocr_required", "ocr-required", "needs_ocr"}:
            return True
    message = str(error).lower()
    return "ocr" in message and any(term in message for term in ("required", "need", "scan", "image"))
