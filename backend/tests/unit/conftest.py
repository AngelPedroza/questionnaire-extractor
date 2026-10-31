import os
from io import BytesIO
from zipfile import ZipFile

import pytest

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.domain.questionnaire import Item, ItemType, Questionnaire


class FakeLLM(QuestionnaireLLM):
    def __init__(self, questionnaire: Questionnaire):
        self.questionnaire = questionnaire
        self.received_texts: list[str] = []

    def extract(self, text: str) -> Questionnaire:
        self.received_texts.append(text)
        return self.questionnaire


@pytest.fixture(autouse=True)
def clear_settings_environment(monkeypatch):
    setting_names = {
        "LLM_PROVIDER",
        "OLLAMA_HOST",
        "OLLAMA_MODEL",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "CORS_ORIGINS",
    }
    for name in tuple(os.environ):
        if name.upper() in setting_names:
            monkeypatch.delenv(name)


@pytest.fixture
def make_questionnaire():
    def make(*, item_count: int = 1, total_items: int | None = None) -> Questionnaire:
        return Questionnaire(
            titulo="Sample questionnaire",
            idioma="en",
            total_items=item_count if total_items is None else total_items,
            items=[
                Item(
                    numero=number,
                    enunciado=f"Question {number}?",
                    tipo=ItemType.desarrollo,
                    alternativas=[],
                    respuesta_correcta=None,
                )
                for number in range(1, item_count + 1)
            ],
        )

    return make


@pytest.fixture
def make_fake_llm():
    return FakeLLM


@pytest.fixture
def make_ooxml():
    def make(main_type: str) -> bytes:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as archive:
            archive.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                f'<Override PartName="/document.xml" ContentType="{main_type}"/>'
                "</Types>",
            )
        return buffer.getvalue()

    return make
