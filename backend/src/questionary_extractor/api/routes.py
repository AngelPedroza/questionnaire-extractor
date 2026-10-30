from fastapi import APIRouter, UploadFile

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.adapters.readers import reader_mapper
from questionary_extractor.application.extract_questionnaire import ExtractQuestionnaire
from questionary_extractor.config import settings
from questionary_extractor.domain.file_type import MAX_FILE_BYTES
from questionary_extractor.domain.questionnaire import Questionnaire

router = APIRouter()
extractor = ExtractQuestionnaire(QuestionnaireLLM.from_settings(settings), reader_mapper)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/upload", response_model=Questionnaire)
def upload(file: UploadFile) -> Questionnaire:
    # Read one byte past the limit so oversized uploads are rejected without loading them whole.
    return extractor(file.filename or "", file.file.read(MAX_FILE_BYTES + 1))
