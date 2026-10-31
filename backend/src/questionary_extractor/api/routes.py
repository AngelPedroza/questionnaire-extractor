import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.adapters.readers import reader_mapper
from questionary_extractor.application.extract_questionnaire import ExtractQuestionnaire
from questionary_extractor.config import settings
from questionary_extractor.domain.errors import ProcessingError, QuestionnaireError
from questionary_extractor.domain.file_type import MAX_FILE_BYTES
from questionary_extractor.domain.questionnaire import Questionnaire

logger = logging.getLogger(__name__)

router = APIRouter()
extractor = ExtractQuestionnaire(
    QuestionnaireLLM.from_settings(settings), reader_mapper
)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/upload", response_model=Questionnaire)
def upload(
    # A list collects every part named "file"; a single UploadFile would silently keep the last.
    files: Annotated[list[UploadFile], File(alias="file")],
) -> Questionnaire:
    if len(files) != 1:
        raise HTTPException(
            status_code=422, detail="Send exactly one file per request."
        )
    file = files[0]
    try:
        # Read one byte past the limit without loading oversized uploads whole.
        return extractor(file.filename or "", file.file.read(MAX_FILE_BYTES + 1))
    except QuestionnaireError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while processing upload")
        raise ProcessingError() from exc
