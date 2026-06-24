#!/usr/bin/env python3
"""Generate binary test fixtures for PDF, DOCX, and Excel.

Run once (or after changing fixture content):
  uv run --group dev tests/generate_fixtures.py

Outputs files to tests/data/{pdf,docx,excel}/.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def generate_pdf():
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 10, "Knowledge Project Skills - Test Document",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 8, (
        "This is a test PDF used to verify the PDF preprocessor. "
        "It contains multiple paragraphs with entities and facts."
    ))
    pdf.ln(4)
    pdf.multi_cell(0, 8, (
        "Alice founded Acme Corp in Paris in 2010. "
        "The company grew to 500 employees by 2020 and was acquired by GlobalTech in 2023."
    ))
    pdf.add_page()
    pdf.set_font("Helvetica", "B", size=12)
    pdf.cell(0, 10, "Second Page", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 8, "Key fact: revenue reached 50M EUR in 2022.")

    out = DATA_DIR / "pdf/sample.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    print(f"  wrote {out}")


def generate_docx():
    import docx

    doc = docx.Document()
    doc.add_heading("Knowledge Project Skills — Test Document", level=1)
    doc.add_paragraph(
        "This is a test Word document used to verify the DOCX preprocessor. "
        "It contains headings, paragraphs, and a table."
    )
    doc.add_heading("Background", level=2)
    doc.add_paragraph(
        "Alice founded Acme Corp in Paris in 2010. "
        "Bob joined as CTO in 2012. The company raised Series A in 2015."
    )
    table = doc.add_table(rows=3, cols=3)
    table.style = "Table Grid"
    headers = ["Name", "Role", "Year"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    table.rows[1].cells[0].text = "Alice"
    table.rows[1].cells[1].text = "CEO"
    table.rows[1].cells[2].text = "2010"
    table.rows[2].cells[0].text = "Bob"
    table.rows[2].cells[1].text = "CTO"
    table.rows[2].cells[2].text = "2012"

    out = DATA_DIR / "docx/sample.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    print(f"  wrote {out}")


def generate_excel():
    import openpyxl

    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "People"
    ws1.append(["name", "age", "city", "score"])
    ws1.append(["Alice", 30, "Paris", 95.5])
    ws1.append(["Bob", 25, "Lyon", 87.3])
    ws1.append(["Carol", 35, "Berlin", 92.1])

    ws2 = wb.create_sheet("Events")
    ws2.append(["date", "event", "location"])
    ws2.append(["2010-01-15", "Company founded", "Paris"])
    ws2.append(["2015-06-01", "Series A", "London"])
    ws2.append(["2023-03-10", "Acquisition", "New York"])

    out = DATA_DIR / "excel/sample.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    print(f"  wrote {out}")


if __name__ == "__main__":
    print("Generating binary test fixtures...")
    generate_pdf()
    generate_docx()
    generate_excel()
    print("Done.")
