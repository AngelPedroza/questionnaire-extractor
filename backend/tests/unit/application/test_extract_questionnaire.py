import pytest

from questionary_extractor.application import extract_questionnaire
from questionary_extractor.application.extract_questionnaire import ExtractQuestionnaire
from questionary_extractor.domain.errors import (
    NoItemsDetectedError,
    UnsupportedFileError,
)


@pytest.mark.parametrize("text", ["", " \t\n"])
def test_blank_reader_text_raises_no_items_without_calling_llm(
    text, make_fake_llm, make_questionnaire
):
    llm = make_fake_llm(make_questionnaire())
    extractor = ExtractQuestionnaire(llm, lambda file_type, content: text)

    with pytest.raises(NoItemsDetectedError) as error:
        extractor("questionnaire.pdf", b"%PDF-1.7")

    assert str(error.value) == "No text could be extracted from the file."
    assert llm.received_texts == []


def test_empty_llm_items_raise_no_items(make_fake_llm, make_questionnaire):
    llm = make_fake_llm(make_questionnaire(item_count=0))
    extractor = ExtractQuestionnaire(llm, lambda file_type, content: "Document text")

    with pytest.raises(NoItemsDetectedError) as error:
        extractor("questionnaire.pdf", b"%PDF-1.7")

    assert str(error.value) == "No questionnaire items were detected."


def test_validation_error_stops_before_reader_and_llm(
    monkeypatch, make_fake_llm, make_questionnaire
):
    # Validation rules are covered in test_file_type.py; here only the flow matters.
    validation_error = UnsupportedFileError("Any validation failure.")

    def failing_validate_file(filename, content):
        raise validation_error

    monkeypatch.setattr(extract_questionnaire, "validate_file", failing_validate_file)
    llm = make_fake_llm(make_questionnaire())
    reader_calls = []

    def spy_reader(file_type, content):
        reader_calls.append((file_type, content))
        return "Document text"

    extractor = ExtractQuestionnaire(llm, spy_reader)

    with pytest.raises(UnsupportedFileError) as error:
        extractor("questionnaire.pdf", b"any content")

    assert error.value is validation_error
    assert reader_calls == []
    assert llm.received_texts == []


def test_extraction_recomputes_total_items(make_fake_llm, make_questionnaire):
    questionnaire = make_questionnaire(item_count=2, total_items=99)
    llm = make_fake_llm(questionnaire)
    extractor = ExtractQuestionnaire(llm, lambda file_type, content: "Document text")

    result = extractor("questionnaire.pdf", b"%PDF-1.7")

    assert result.total_items == 2
    assert result.items == questionnaire.items
    assert result.titulo == questionnaire.titulo
    assert result.idioma == questionnaire.idioma
    assert questionnaire.total_items == 99


def test_reader_receives_detected_type_and_original_bytes(
    make_fake_llm, make_questionnaire
):
    llm = make_fake_llm(make_questionnaire())
    reader_calls = []
    content = b"%PDF-1.7"

    def reader(file_type, received_content):
        reader_calls.append((file_type, received_content))
        return "Document text"

    extractor = ExtractQuestionnaire(llm, reader)

    extractor("questionnaire.pdf", content)

    assert reader_calls == [("pdf", content)]


def test_llm_receives_reader_text_unchanged(make_fake_llm, make_questionnaire):
    llm = make_fake_llm(make_questionnaire())
    text = "  Document text\n"
    extractor = ExtractQuestionnaire(llm, lambda file_type, content: text)

    extractor("questionnaire.pdf", b"%PDF-1.7")

    assert llm.received_texts == [text]
