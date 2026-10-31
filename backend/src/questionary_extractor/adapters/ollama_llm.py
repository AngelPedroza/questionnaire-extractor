from json import JSONDecodeError

import httpx
import ollama
from pydantic import ValidationError

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.adapters.prompt import SYSTEM_PROMPT
from questionary_extractor.domain.errors import (
    DocumentTooLongError,
    ExtractionError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from questionary_extractor.domain.questionnaire import Questionnaire

# Local development only (production uses Gemini): one generous attempt per request.
TIMEOUT_SECONDS = 180
CONNECT_RETRIES = 2

# Context budget for qwen3.5:9b running locally on an 18 GB laptop.
# - Deliberately small window: Ollama reserves the KV cache for the whole window. Qwen3.5 is
#   hybrid (only 8 of its 32 layers use full attention: 4 KV heads, head dim 256), so the
#   cache costs ~8 x 2 (K, V) x 4 x 256 x 2 bytes ≈ 32 KB per token: 8,192 tokens ≈ 256 MB on
#   top of the 7.6 GB of weights. The model supports 262,144 tokens, but that would need
#   ~8 GB more. Architecture (unofficial, consistent across write-ups):
#   https://apxml.com/models/qwen35-9b
# - The window holds prompt + answer, so the input budget is
#   (NUM_CTX - PROMPT_TOKENS - OUTPUT_RESERVE_TOKENS) * CHARS_PER_TOKEN.
#   Qwen uses byte-level BPE with a 248,320-token vocabulary
#   (https://huggingface.co/Qwen/Qwen3.5-9B); 3.5 chars/token is a conservative rule of
#   thumb for es/it/en, not a measured value. Measure it with `prompt_eval_count` in the
#   Ollama response.
NUM_CTX = 8_192
PROMPT_TOKENS = 1_000  # system prompt + JSON schema (~2,780 chars today)
OUTPUT_RESERVE_TOKENS = 2_500  # JSON answer for ~20 items
CHARS_PER_TOKEN = 3.5
MAX_INPUT_CHARS = int(
    (NUM_CTX - PROMPT_TOKENS - OUTPUT_RESERVE_TOKENS) * CHARS_PER_TOKEN
)  # ≈ 16,400
# No keep_alive: Ollama's default (5 min) unloads the 7.6 GB model when idle to free memory.


class OllamaQuestionnaireLLM(QuestionnaireLLM):
    def __init__(
        self, host: str, model: str, transport: httpx.BaseTransport | None = None
    ):
        self.client = ollama.Client(
            host=host,
            timeout=TIMEOUT_SECONDS,
            transport=transport or httpx.HTTPTransport(retries=CONNECT_RETRIES),
        )
        self.model = model

    def extract(self, text: str) -> Questionnaire:
        if len(text) > MAX_INPUT_CHARS:
            raise DocumentTooLongError()
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                format=Questionnaire.model_json_schema(),
                think=False,
                options={"temperature": 0, "num_ctx": NUM_CTX},
            )
            return Questionnaire.model_validate_json(response.message.content)
        except (ConnectionError, httpx.ConnectTimeout) as exc:
            raise LLMUnavailableError("The language model is not reachable.") from exc
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError() from exc
        except (ollama.ResponseError, ValidationError, JSONDecodeError) as exc:
            raise ExtractionError(
                "The language model returned an invalid response."
            ) from exc
