"""Plain-text readers for the supported file formats.

Technical decision: readers are plain functions dispatched through a dict instead of a
DocumentReader ABC with one subclass per format. They hold no state, so a class per
format would only wrap a single method ("Stop Writing Classes", PyCon 2012), and a dict
of functions is the idiomatic Strategy pattern in Python (Fluent Python, 2nd ed., ch. 10).
Project rule: stateful adapters (e.g. LLM clients) are classes implementing an ABC;
stateless helpers are functions. Revisit if a reader ever needs state or configuration.
"""

from io import BytesIO

import pdfplumber
from docx import Document
from openpyxl import load_workbook

from questionary_extractor.domain.errors import UnsupportedFileError


def read_pdf(content: bytes) -> str:
    try:
        with pdfplumber.open(BytesIO(content)) as document:
            return "\n".join(page.extract_text() or "" for page in document.pages)
    except Exception as exc:
        raise UnsupportedFileError(
            "The file could not be read; it may be corrupted."
        ) from exc


def read_docx(content: bytes) -> str:
    try:
        document = Document(BytesIO(content))
        lines = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        for table in document.tables:
            for row in table.rows:
                lines.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(lines)
    except Exception as exc:
        raise UnsupportedFileError(
            "The file could not be read; it may be corrupted."
        ) from exc


def read_xlsx(content: bytes) -> str:
    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        try:
            lines = []
            for sheet in workbook:
                lines.append(f"# {sheet.title}")
                for row in sheet.iter_rows(values_only=True):
                    lines.append(
                        " | ".join(
                            str(cell) for cell in row if cell is not None and cell != ""
                        )
                    )
            return "\n".join(lines)
        finally:
            workbook.close()
    except Exception as exc:
        raise UnsupportedFileError(
            "The file could not be read; it may be corrupted."
        ) from exc


READERS = {"pdf": read_pdf, "docx": read_docx, "xlsx": read_xlsx}


def reader_mapper(file_type: str, content: bytes) -> str:
    return READERS[file_type](content)
