from fastapi import Request
from fastapi.responses import JSONResponse

from questionary_extractor.domain.errors import (
    DocumentTooLongError,
    ExtractionError,
    FileTooLargeError,
    LLMTimeoutError,
    LLMUnavailableError,
    NoItemsDetectedError,
    ProcessingError,
    QuestionnaireError,
    UnsupportedFileError,
)

STATUS_BY_ERROR = {
    UnsupportedFileError: 415,
    FileTooLargeError: 413,
    DocumentTooLongError: 413,
    LLMTimeoutError: 504,
    ProcessingError: 500,
    NoItemsDetectedError: 422,
    ExtractionError: 502,
    LLMUnavailableError: 503,
}


def questionnaire_error_handler(
    request: Request, exc: QuestionnaireError
) -> JSONResponse:
    return JSONResponse(
        status_code=STATUS_BY_ERROR.get(type(exc), 500),
        content={"detail": str(exc)},
    )
