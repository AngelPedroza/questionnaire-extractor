import time
from collections.abc import Callable
from threading import Lock

from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.domain.errors import LLMTimeoutError, LLMUnavailableError
from questionary_extractor.domain.questionnaire import Questionnaire

# Stop occupying workers after three failures and allow one trial after 30 s.
FAILURE_THRESHOLD = 3
RESET_TIMEOUT = 30.0
OPEN_MESSAGE = (
    "The language model is temporarily unavailable. Please try again in a few seconds."
)


class CircuitBreakerLLM(QuestionnaireLLM):
    def __init__(
        self,
        inner: QuestionnaireLLM,
        failure_threshold: int = FAILURE_THRESHOLD,
        reset_timeout: float = RESET_TIMEOUT,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.inner = inner
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.clock = clock
        self._lock = Lock()
        self._failures = 0
        self._opened_at: float | None = None
        self._trial = False
        self._generation = 0

    def extract(self, text: str) -> Questionnaire:
        with self._lock:
            trial = self._opened_at is not None
            if trial:
                if self._trial or self.clock() - self._opened_at < self.reset_timeout:
                    raise LLMUnavailableError(OPEN_MESSAGE)
                self._trial = True
            generation = self._generation
        try:
            result = self.inner.extract(text)
        except (LLMUnavailableError, LLMTimeoutError):
            with self._lock:
                if generation == self._generation:
                    self._failures += 1
                    if trial or self._failures >= self.failure_threshold:
                        self._opened_at = self.clock()
                        self._generation += 1
                        self._trial = False
            raise
        except Exception:
            if trial:
                self._close(generation)
            raise
        self._close(generation)
        return result

    def _close(self, generation: int) -> None:
        with self._lock:
            # Ignore calls admitted before a newer open/half-open cycle.
            if generation == self._generation:
                self._failures = 0
                self._opened_at = None
                self._trial = False
