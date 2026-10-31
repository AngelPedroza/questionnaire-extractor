import json

import pytest
from starlette.requests import Request

from questionary_extractor.api.errors import questionnaire_error_handler
from questionary_extractor.domain.errors import (
    ExtractionError,
    FileTooLargeError,
    LLMUnavailableError,
    NoItemsDetectedError,
    QuestionnaireError,
    UnsupportedFileError,
)


@pytest.mark.parametrize(
    ("error_type", "message", "status_code"),
    [
        (NoItemsDetectedError, "No text could be extracted from the file.", 422),
        (NoItemsDetectedError, "No questionnaire items were detected.", 422),
        (UnsupportedFileError, "The file is empty.", 415),
        (
            UnsupportedFileError,
            "Unsupported, corrupted or unrecognized file.",
            415,
        ),
        (
            UnsupportedFileError,
            "File content is pdf, but the name says .docx.",
            415,
        ),
        (FileTooLargeError, "The file must be 4 MB or smaller.", 413),
        (LLMUnavailableError, "The language model is not reachable.", 503),
        (
            ExtractionError,
            "The language model returned an invalid response.",
            502,
        ),
        (QuestionnaireError, "An unexpected questionnaire error occurred.", 500),
    ],
)
def test_handler_returns_error_status_and_exact_message(
    error_type, message, status_code
):
    response = questionnaire_error_handler(
        Request({"type": "http"}), error_type(message)
    )

    assert response.status_code == status_code
    assert json.loads(response.body) == {"detail": message}


@pytest.mark.parametrize(
    ("name", "message", "status_code"),
    [
        (
            "LLMTimeoutError",
            "The document took too long to process. Try a smaller file.",
            504,
        ),
        (
            "DocumentTooLongError",
            "The document is too long to process. Try a shorter file.",
            413,
        ),
        (
            "ProcessingError",
            "Something went wrong while processing the file. Please try again.",
            500,
        ),
    ],
)
def test_resilience_errors_have_default_message_and_http_status(
    name, message, status_code
):
    from questionary_extractor.domain import errors

    error_type = getattr(errors, name, None)
    assert error_type is not None, f"Missing domain error: {name}"
    error = error_type()
    assert isinstance(error, QuestionnaireError)
    response = questionnaire_error_handler(Request({"type": "http"}), error)

    assert response.status_code == status_code
    assert json.loads(response.body) == {"detail": message}
