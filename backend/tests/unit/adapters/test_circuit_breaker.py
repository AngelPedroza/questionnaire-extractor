from threading import Event, Thread

import pytest

from questionary_extractor.adapters.circuit_breaker import CircuitBreakerLLM
from questionary_extractor.adapters.llm import QuestionnaireLLM
from questionary_extractor.domain import errors

OPEN_MESSAGE = (
    "The language model is temporarily unavailable. Please try again in a few seconds."
)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class FakeLLM(QuestionnaireLLM):
    def __init__(self, result):
        self.result = result
        self.error = None
        self.calls = []

    def extract(self, text):
        self.calls.append(text)
        if self.error:
            raise self.error
        return self.result


def trip(breaker, inner):
    inner.error = errors.LLMUnavailableError("offline")
    for _ in range(3):
        with pytest.raises(errors.LLMUnavailableError, match="offline"):
            breaker.extract("Document text")


def test_passes_text_and_result_through(make_questionnaire):
    expected = make_questionnaire()
    inner = FakeLLM(expected)
    breaker = CircuitBreakerLLM(inner)

    assert isinstance(breaker, QuestionnaireLLM)
    assert breaker.extract("Document text") is expected
    assert inner.calls == ["Document text"]


@pytest.mark.parametrize("error_name", ["LLMUnavailableError", "LLMTimeoutError"])
def test_opens_after_three_infrastructure_failures(make_questionnaire, error_name):
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner)
    inner.error = getattr(errors, error_name)("infrastructure failure")
    for _ in range(3):
        with pytest.raises(type(inner.error), match="infrastructure failure"):
            breaker.extract("Document text")

    with pytest.raises(errors.LLMUnavailableError) as error:
        breaker.extract("Blocked text")

    assert str(error.value) == OPEN_MESSAGE
    assert len(inner.calls) == 3


@pytest.mark.parametrize("error_name", ["ExtractionError", "DocumentTooLongError"])
def test_content_errors_do_not_count(make_questionnaire, error_name):
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner)
    inner.error = getattr(errors, error_name)("bad document")
    for _ in range(4):
        with pytest.raises(type(inner.error), match="bad document"):
            breaker.extract("Document text")

    inner.error = None
    assert breaker.extract("Valid text") is inner.result
    assert len(inner.calls) == 5


def test_success_resets_consecutive_failure_count(make_questionnaire):
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner)
    inner.error = errors.LLMUnavailableError("offline")
    for _ in range(2):
        with pytest.raises(errors.LLMUnavailableError):
            breaker.extract("Document text")
    inner.error = None
    breaker.extract("Recovered text")

    trip(breaker, inner)
    assert len(inner.calls) == 6
    with pytest.raises(errors.LLMUnavailableError, match="temporarily unavailable"):
        breaker.extract("Blocked text")
    assert len(inner.calls) == 6


def test_stays_open_until_reset_timeout(make_questionnaire):
    clock = FakeClock()
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner, clock=clock)
    trip(breaker, inner)
    clock.now = 29.999

    with pytest.raises(errors.LLMUnavailableError, match="temporarily unavailable"):
        breaker.extract("Too soon")

    assert len(inner.calls) == 3


def test_half_open_success_closes(make_questionnaire):
    clock = FakeClock()
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner, clock=clock)
    trip(breaker, inner)
    clock.now = 30.0
    inner.error = None

    assert breaker.extract("Trial") is inner.result
    assert breaker.extract("Closed") is inner.result
    assert inner.calls[-2:] == ["Trial", "Closed"]


def test_half_open_failure_reopens_for_full_cooldown(make_questionnaire):
    clock = FakeClock()
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner, clock=clock)
    trip(breaker, inner)
    clock.now = 30.0
    with pytest.raises(errors.LLMUnavailableError, match="offline"):
        breaker.extract("Trial")
    clock.now = 59.999
    with pytest.raises(errors.LLMUnavailableError, match="temporarily unavailable"):
        breaker.extract("Blocked")
    assert len(inner.calls) == 4
    clock.now = 60.0
    inner.error = None
    assert breaker.extract("Recovery") is inner.result


def test_half_open_allows_only_one_trial(make_questionnaire):
    clock = FakeClock()
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner, clock=clock)
    trip(breaker, inner)
    clock.now = 30.0
    entered = Event()
    release = Event()
    results = []

    def trial(text):
        entered.set()
        assert release.wait(2)
        return inner.result

    inner.extract = trial
    thread = Thread(target=lambda: results.append(breaker.extract("Trial")))
    thread.start()
    try:
        assert entered.wait(2)
        with pytest.raises(errors.LLMUnavailableError, match="temporarily unavailable"):
            breaker.extract("Concurrent request")
    finally:
        release.set()
        thread.join(2)

    assert not thread.is_alive()
    assert results == [inner.result]


@pytest.mark.parametrize(
    "error_name", ["ExtractionError", "DocumentTooLongError", "RuntimeError"]
)
def test_half_open_non_infrastructure_error_does_not_leave_trial_stuck(
    make_questionnaire, error_name
):
    clock = FakeClock()
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner, clock=clock)
    trip(breaker, inner)
    clock.now = 30.0
    error_type = (
        RuntimeError if error_name == "RuntimeError" else getattr(errors, error_name)
    )
    inner.error = error_type("not infrastructure")
    with pytest.raises(error_type, match="not infrastructure"):
        breaker.extract("Trial")
    inner.error = None

    assert breaker.extract("Next request") is inner.result


def test_configurable_threshold_and_reset_timeout(make_questionnaire):
    clock = FakeClock()
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(
        inner, failure_threshold=1, reset_timeout=5, clock=clock
    )
    inner.error = errors.LLMUnavailableError("offline")
    with pytest.raises(errors.LLMUnavailableError, match="offline"):
        breaker.extract("Failure")
    with pytest.raises(errors.LLMUnavailableError, match="temporarily unavailable"):
        breaker.extract("Blocked")
    assert len(inner.calls) == 1
    clock.now = 5
    inner.error = None
    assert breaker.extract("Trial") is inner.result


def test_in_flight_success_cannot_close_newly_opened_breaker(make_questionnaire):
    inner = FakeLLM(make_questionnaire())
    breaker = CircuitBreakerLLM(inner)
    entered = Event()
    release = Event()
    results = []
    extract = inner.extract

    def delayed(text):
        if text == "Slow success":
            entered.set()
            assert release.wait(2)
            return inner.result
        return extract(text)

    inner.extract = delayed
    thread = Thread(target=lambda: results.append(breaker.extract("Slow success")))
    thread.start()
    try:
        assert entered.wait(2)
        trip(breaker, inner)
    finally:
        release.set()
        thread.join(2)

    assert results == [inner.result]
    with pytest.raises(errors.LLMUnavailableError, match="temporarily unavailable"):
        breaker.extract("Still blocked")
    assert len(inner.calls) == 3
