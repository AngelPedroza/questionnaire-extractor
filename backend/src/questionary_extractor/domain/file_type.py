import zipfile
from io import BytesIO

from questionary_extractor.domain.errors import FileTooLargeError, UnsupportedFileError

MAX_FILE_BYTES = 4 * 1024 * 1024  # Vercel rejects bodies > 4.5 MB
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024  # zip-bomb guard
OOXML_MAIN_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml": "xlsx",
}


def detect_file_type(content: bytes) -> str | None:
    if content.startswith(b"%PDF-"):
        return "pdf"
    if not content.startswith(b"PK\x03\x04"):
        return None

    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            if (
                sum(info.file_size for info in archive.infolist())
                > MAX_UNCOMPRESSED_BYTES
            ):
                return None
            content_types = archive.read("[Content_Types].xml").decode(
                "utf-8", "replace"
            )
    except (zipfile.BadZipFile, KeyError):
        return None

    return next(
        (
            ext
            for main_type, ext in OOXML_MAIN_TYPES.items()
            if main_type in content_types
        ),
        None,
    )


def validate_file(filename: str, content: bytes) -> str:
    if not content:
        raise UnsupportedFileError("The file is empty.")
    if len(content) > MAX_FILE_BYTES:
        raise FileTooLargeError("The file must be 4 MB or smaller.")

    real = detect_file_type(content)
    if real is None:
        raise UnsupportedFileError("Unsupported, corrupted or unrecognized file.")
    declared = filename.rsplit(".", 1)[-1].lower()
    if declared != real:
        raise UnsupportedFileError(
            f"File content is {real}, but the name says .{declared}."
        )
    return real
