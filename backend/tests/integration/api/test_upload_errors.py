import logging

import pytest
from fastapi.testclient import TestClient

from questionary_extractor.domain.errors import (
    DocumentTooLongError,
    ExtractionError,
    FileTooLargeError,
    LLMTimeoutError,
    LLMUnavailableError,
    NoItemsDetectedError,
    ProcessingError,
    UnsupportedFileError,
)


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (UnsupportedFileError("Unsupported, corrupted or unrecognized file."), 415),
        (FileTooLargeError("The file must be 4 MB or smaller."), 413),
        (DocumentTooLongError(), 413),
        (NoItemsDetectedError("No questionnaire items were detected."), 422),
        (ExtractionError("The language model returned an invalid response."), 502),
        (LLMUnavailableError("The language model is not reachable."), 503),
        (
            LLMUnavailableError(
                "The language model is temporarily unavailable. Please try again in a few seconds."
            ),
            503,
        ),
        (LLMTimeoutError(), 504),
        (ProcessingError(), 500),
    ],
)
def test_upload_returns_domain_error_message(monkeypatch, error, status):
    from questionary_extractor.api import routes
    from questionary_extractor.main import app

    def fail(filename, content):
        assert filename == "questionnaire.pdf"
        assert content == b"document"
        raise error

    monkeypatch.setattr(routes, "extractor", fail)
    with TestClient(app) as client:
        response = client.post(
            "/upload",
            files={"file": ("questionnaire.pdf", b"document", "application/pdf")},
            headers={"Origin": "http://localhost:3000"},
        )

    assert response.status_code == status
    assert response.json() == {"detail": str(error)}
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_unexpected_failure_returns_generic_message_with_cors_and_app_stays_up(
    monkeypatch, caplog
):
    from questionary_extractor.api import routes
    from questionary_extractor.main import app

    failure = RuntimeError("internal details must not reach the response")

    def fail(filename, content):
        raise failure

    monkeypatch.setattr(routes, "extractor", fail)
    with (
        caplog.at_level(logging.ERROR, logger=routes.__name__),
        TestClient(app) as client,
    ):
        response = client.post(
            "/upload",
            files={"file": ("questionnaire.pdf", b"document", "application/pdf")},
            headers={"Origin": "http://localhost:3000"},
        )
        health = client.get("/health")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Something went wrong while processing the file. Please try again."
    }
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    records = [record for record in caplog.records if record.name == routes.__name__]
    assert len(records) == 1
    assert records[0].exc_info[1] is failure
