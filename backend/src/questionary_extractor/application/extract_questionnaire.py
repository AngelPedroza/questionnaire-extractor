import logging
from collections.abc import Callable
from time import perf_counter

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.domain.errors import NoItemsDetectedError
from questionary_extractor.domain.file_type import validate_file
from questionary_extractor.domain.questionnaire import Questionnaire

logger = logging.getLogger(__name__)


class ExtractQuestionnaire:
    def __init__(self, llm: QuestionnaireLLM, reader_mapper: Callable[[str, bytes], str]):
        self.llm = llm
        self.reader_mapper = reader_mapper

    def __call__(self, filename: str, content: bytes) -> Questionnaire:
        started = perf_counter()
        file_type = validate_file(filename, content)
        text = self.reader_mapper(file_type, content)
        
        if not text.strip():
            raise NoItemsDetectedError("No text could be extracted from the file.")
        questionnaire = self.llm.extract(text)
        
        if not questionnaire.items:
            raise NoItemsDetectedError("No questionnaire items were detected.")
        
        logger.info(
            "Extracted %s file: %d items in %.3f seconds",
            file_type,
            len(questionnaire.items),
            perf_counter() - started,
        )
        
        return questionnaire.model_copy(
            update={"total_items": len(questionnaire.items)}
        )
