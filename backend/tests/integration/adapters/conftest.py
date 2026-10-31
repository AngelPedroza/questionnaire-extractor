from collections import deque

import httpx
import pytest

from questionary_extractor.domain.questionnaire import Questionnaire


class RecordingHandler:
    def __init__(self, outcomes):
        self.outcomes = deque(outcomes)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        assert self.outcomes, "Unexpected additional LLM request"
        outcome = self.outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def recording_handler():
    return RecordingHandler


@pytest.fixture
def questionnaire():
    return Questionnaire.model_validate(
        {
            "titulo": "Sample questionnaire",
            "idioma": "en",
            "total_items": 1,
            "items": [
                {
                    "numero": 1,
                    "enunciado": "How are you?",
                    "tipo": "desarrollo",
                    "alternativas": [],
                    "respuesta_correcta": None,
                }
            ],
        }
    )


@pytest.fixture
def ollama_response(questionnaire):
    def make(content=None):
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "message": {
                    "role": "assistant",
                    "content": questionnaire.model_dump_json()
                    if content is None
                    else content,
                },
                "done": True,
            },
        )

    return make


@pytest.fixture
def gemini_response(questionnaire):
    def make(text=None):
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "text": questionnaire.model_dump_json()
                                    if text is None
                                    else text
                                }
                            ],
                        },
                        "finishReason": "STOP",
                        "index": 0,
                    }
                ]
            },
        )

    return make
