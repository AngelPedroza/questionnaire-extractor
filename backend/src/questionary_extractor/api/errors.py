from fastapi import Request
from fastapi.responses import JSONResponse

from questionary_extractor.domain.errors import (
    ExtractionError,
    FileTooLargeError,
    LLMUnavailableError,
    NoItemsDetectedError,
    QuestionnaireError,
    UnsupportedFileError,
)

STATUS_BY_ERROR = {
    UnsupportedFileError: 415,
    FileTooLargeError: 413,
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
