from pathlib import Path

from openpyxl import Workbook
from reportlab.pdfgen.canvas import Canvas

from sc_education_finance.adapters import (
    read_csv_rows,
    read_html_rows,
    read_pdf_text,
    read_workbook_rows,
)


def test_invented_pdf_html_csv_and_workbook_fixtures(tmp_path: Path) -> None:
    pdf = tmp_path / "invented.pdf"
    canvas = Canvas(str(pdf))
    canvas.drawString(72, 720, "Zone Alpha synthetic value 42")
    canvas.save()
    assert "Zone Alpha synthetic value 42" in read_pdf_text(pdf)

    html = tmp_path / "invented.html"
    html.write_text(
        "<table><tr><th>zone</th><th>value</th></tr>"
        "<tr><td>Alpha</td><td>42</td></tr></table>",
        encoding="utf-8",
    )
    assert read_html_rows(html)[1] == ["Alpha", "42"]

    csv_path = tmp_path / "invented.csv"
    csv_path.write_text("zone,value\nAlpha,42\n", encoding="utf-8")
    assert read_csv_rows(csv_path) == [{"zone": "Alpha", "value": "42"}]

    workbook_path = tmp_path / "invented.xlsx"
    workbook = Workbook()
    workbook.active.append(["zone", "value"])
    workbook.active.append(["Alpha", 42])
    workbook.save(workbook_path)
    assert read_workbook_rows(workbook_path)[1] == ["Alpha", 42]
