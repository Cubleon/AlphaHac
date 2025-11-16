import io

from docx import Document
from PyPDF2 import PdfReader
import pandas as pd
import comtypes.client


def docx_to_text(bytes: io.BytesIO) -> str:
    doc = Document(bytes)
    parts = [p.text for p in doc.paragraphs if p.text]
    for table in doc.tables:
        for row in table.rows:
            row_text = ""
            for cell in row.cells:
                if cell.text:
                    row_text += cell.text + " "
            parts.append(row_text)
    return "\n".join(parts).strip()


def pdf_to_text(bytes: io.BytesIO) -> str:
    reader = PdfReader(bytes)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def excel_to_text(bytes: io.BytesIO) -> str:
    table = pd.read_excel(bytes)
    return table.to_string(index=False)
