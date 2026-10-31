from io import BytesIO
from zipfile import ZipFile

import pytest

from questionary_extractor.domain import file_type
from questionary_extractor.domain.errors import FileTooLargeError, UnsupportedFileError
from questionary_extractor.domain.file_type import detect_file_type, validate_file

DOCX_MAIN_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)
XLSX_MAIN_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
)


@pytest.fixture
def plain_zip():
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("notes.txt", "Not an Office document.")
    return buffer.getvalue()


def test_validate_file_rejects_empty_content():
    with pytest.raises(UnsupportedFileError) as error:
        validate_file("questionnaire.pdf", b"")

    assert str(error.value) == "The file is empty."


def test_validate_file_rejects_content_over_size_limit(monkeypatch):
    monkeypatch.setattr(file_type, "MAX_FILE_BYTES", 5)

    with pytest.raises(FileTooLargeError) as error:
        validate_file("questionnaire.pdf", b"%PDF-1")

    assert str(error.value) == "The file must be 4 MB or smaller."


@pytest.mark.parametrize("content", [b"MZunknown", b"PK\x03\x04corrupted"])
def test_validate_file_rejects_unknown_or_corrupted_content(content):
    with pytest.raises(UnsupportedFileError) as error:
        validate_file("questionnaire.docx", content)

    assert str(error.value) == "Unsupported, corrupted or unrecognized file."


def test_validate_file_rejects_zip_without_content_types(plain_zip):
    with pytest.raises(UnsupportedFileError) as error:
        validate_file("questionnaire.docx", plain_zip)

    assert str(error.value) == "Unsupported, corrupted or unrecognized file."


def test_validate_file_rejects_unknown_ooxml_type(make_ooxml):
    with pytest.raises(UnsupportedFileError) as error:
        validate_file("questionnaire.docx", make_ooxml("application/unknown"))

    assert str(error.value) == "Unsupported, corrupted or unrecognized file."


def test_validate_file_rejects_zip_over_uncompressed_size_limit(
    monkeypatch, make_ooxml
):
    monkeypatch.setattr(file_type, "MAX_UNCOMPRESSED_BYTES", 1)

    with pytest.raises(UnsupportedFileError) as error:
        validate_file("questionnaire.docx", make_ooxml(DOCX_MAIN_TYPE))

    assert str(error.value) == "Unsupported, corrupted or unrecognized file."


def test_validate_file_rejects_extension_mismatching_content():
    with pytest.raises(UnsupportedFileError) as error:
        validate_file("questionnaire.docx", b"%PDF-1.7")

    assert str(error.value) == "File content is pdf, but the name says .docx."


def test_detect_file_type_recognizes_pdf_signature():
    assert detect_file_type(b"%PDF-1.7") == "pdf"


@pytest.mark.parametrize(
    ("main_type", "expected_type"),
    [(DOCX_MAIN_TYPE, "docx"), (XLSX_MAIN_TYPE, "xlsx")],
)
def test_detect_file_type_recognizes_ooxml(main_type, expected_type, make_ooxml):
    assert detect_file_type(make_ooxml(main_type)) == expected_type


def test_detect_file_type_rejects_zip_without_content_types(plain_zip):
    assert detect_file_type(plain_zip) is None


def test_detect_file_type_rejects_unknown_ooxml_type(make_ooxml):
    assert detect_file_type(make_ooxml("application/unknown")) is None


@pytest.mark.parametrize("content", [b"PK\x03\x04corrupted", b"MZunknown"])
def test_detect_file_type_rejects_unknown_or_corrupted_content(content):
    assert detect_file_type(content) is None


def test_detect_file_type_rejects_zip_over_uncompressed_size_limit(
    monkeypatch, make_ooxml
):
    monkeypatch.setattr(file_type, "MAX_UNCOMPRESSED_BYTES", 1)

    assert detect_file_type(make_ooxml(DOCX_MAIN_TYPE)) is None


def test_validate_file_accepts_uppercase_extension():
    assert validate_file("questionnaire.PDF", b"%PDF-1.7") == "pdf"


@pytest.mark.parametrize(
    ("extension", "main_type"),
    [("pdf", None), ("docx", DOCX_MAIN_TYPE), ("xlsx", XLSX_MAIN_TYPE)],
)
def test_validate_file_accepts_matching_content_and_extension(
    extension, main_type, make_ooxml
):
    content = b"%PDF-1.7" if main_type is None else make_ooxml(main_type)

    assert validate_file(f"questionnaire.{extension}", content) == extension


def test_validate_file_accepts_content_at_size_limit(monkeypatch):
    content = b"%PDF-1.7"
    monkeypatch.setattr(file_type, "MAX_FILE_BYTES", len(content))

    assert validate_file("questionnaire.pdf", content) == "pdf"
