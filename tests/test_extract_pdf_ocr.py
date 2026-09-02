import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).parent.parent / "skills/kp-staging/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pdf_ocr  # noqa: E402


def test_text_only_mode_does_not_request_ocr():
    settings = pdf_ocr.OcrSettings.from_args("auto", "eng", ".kp-cache/ocr")
    assert settings.mode == "auto"
    assert settings.languages == ("eng",)


def test_language_codes_accept_comma_and_plus_separators():
    assert pdf_ocr.normalize_languages("eng,fra+deu") == ("eng", "fra", "deu")


def test_cache_reuse_and_invalidation(tmp_path, monkeypatch):
    source = tmp_path / "scanned.pdf"
    source.write_bytes(b"original PDF bytes")
    settings = pdf_ocr.OcrSettings.from_args("force", "eng", str(tmp_path / "cache"))
    calls = []

    monkeypatch.setattr(pdf_ocr, "check_dependencies", lambda languages: None)

    def fake_run(command, **_kwargs):
        calls.append(command)
        Path(command[-1]).write_bytes(b"OCR derivative")

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr(pdf_ocr.subprocess, "run", fake_run)

    first_path, first_hash, created = pdf_ocr.create_derivative(source, settings)
    assert created is True
    assert first_path.exists()
    assert first_hash == pdf_ocr.source_sha256(source)
    assert calls[0][1:4] == ["--skip-text", "--deskew", "--rotate-pages"]

    reused_path, reused_hash, created = pdf_ocr.create_derivative(source, settings)
    assert (reused_path, reused_hash, created) == (first_path, first_hash, False)
    assert len(calls) == 1

    source.write_bytes(b"changed PDF bytes")
    changed_path, _, _ = pdf_ocr.create_derivative(source, settings)
    french_settings = pdf_ocr.OcrSettings.from_args("force", "eng+fra", str(tmp_path / "cache"))
    language_path, _ = pdf_ocr.cache_path(source, french_settings)
    assert changed_path != first_path
    assert language_path != changed_path


def test_missing_dependency_has_install_and_opt_out_guidance(monkeypatch):
    monkeypatch.setattr(pdf_ocr.shutil, "which", lambda _name: None)
    with pytest.raises(pdf_ocr.OcrDependencyError) as error:
        pdf_ocr.check_dependencies(("eng", "fra"))
    message = str(error.value)
    assert "ocrmypdf" in message
    assert "tesseract-ocr-eng" in message
    assert "ghostscript" in message
    assert "--ocr off" in message


def test_missing_tesseract_language_has_actionable_guidance(monkeypatch):
    monkeypatch.setattr(pdf_ocr.shutil, "which", lambda _name: "/usr/bin/tool")

    class Result:
        returncode = 0
        stdout = "List of available languages in /usr/share/tesseract-ocr:\\neng\\n"

    monkeypatch.setattr(pdf_ocr.subprocess, "run", lambda *_args, **_kwargs: Result())
    with pytest.raises(pdf_ocr.OcrDependencyError, match="Tesseract language data \\(fra\\)"):
        pdf_ocr.check_dependencies(("eng", "fra"))


def test_ocr_required_detection_prefers_typed_code_and_narrow_text_match():
    class TypedError(Exception):
        code = "ocr_required"

    assert pdf_ocr.ocr_required(TypedError())
    assert pdf_ocr.ocr_required(RuntimeError("OCR is required for scanned pages"))
    assert not pdf_ocr.ocr_required(RuntimeError("unsupported PDF encryption"))
