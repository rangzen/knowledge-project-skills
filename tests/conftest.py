import json
import subprocess
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
SCRIPTS_DIR = Path(__file__).parent.parent / "skills/extract/scripts"


def run_preprocessor(script_name: str, data_file: Path) -> dict:
    result = subprocess.run(
        ["uv", "run", str(SCRIPTS_DIR / script_name), str(data_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"{script_name} failed:\n{result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture(scope="session", autouse=True)
def binary_fixtures():
    pdf = DATA_DIR / "pdf/sample.pdf"
    docx = DATA_DIR / "docx/sample.docx"
    excel = DATA_DIR / "excel/sample.xlsx"
    if not (pdf.exists() and docx.exists() and excel.exists()):
        subprocess.run(
            ["uv", "run", "--group", "dev",
             str(Path(__file__).parent / "generate_fixtures.py")],
            check=True,
        )
