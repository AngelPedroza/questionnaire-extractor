import pytest
from pydantic import ValidationError

from questionary_extractor.domain.questionnaire import Option, Questionnaire


@pytest.fixture
def example_payload():
    return {
        "titulo": "Questionario di esempio",
        "idioma": "it",
        "total_items": 2,
        "items": [
            {
                "numero": 1,
                "enunciado": "Mi preoccupo eccessivamente per cose di poca importanza.",
                "tipo": "escala_likert",
                "alternativas": [
                    {"valor": 0, "texto": "Mai"},
                    {"valor": 1, "texto": "A volte"},
                ],
                "respuesta_correcta": None,
            },
            {
                "numero": 2,
                "enunciado": "Quale numero completa la serie: 2, 4, 8, 16, ...?",
                "tipo": "seleccion_multiple",
                "alternativas": [
                    {"valor": "A", "texto": "18"},
                    {"valor": "C", "texto": "32"},
                ],
                "respuesta_correcta": "C",
            },
        ],
    }


def test_brief_example_validates_without_changing_output(example_payload):
    questionnaire = Questionnaire.model_validate(example_payload)

    assert questionnaire.model_dump(mode="json") == example_payload


def test_invalid_item_type_is_rejected(example_payload):
    example_payload["items"][0]["tipo"] = "unknown"

    with pytest.raises(ValidationError) as error:
        Questionnaire.model_validate(example_payload)

    assert error.value.errors()[0]["loc"] == ("items", 0, "tipo")
    assert error.value.errors()[0]["type"] == "enum"


def test_correct_answer_is_required(example_payload):
    del example_payload["items"][0]["respuesta_correcta"]

    with pytest.raises(ValidationError) as error:
        Questionnaire.model_validate(example_payload)

    assert error.value.errors()[0]["loc"] == ("items", 0, "respuesta_correcta")
    assert error.value.errors()[0]["type"] == "missing"


def test_correct_answer_can_be_none(example_payload):
    questionnaire = Questionnaire.model_validate(example_payload)

    assert questionnaire.items[0].respuesta_correcta is None


@pytest.mark.parametrize("value", [1, "A"])
def test_option_value_accepts_integer_or_string(value):
    option = Option(valor=value, texto="Answer")

    assert option.valor == value
    assert type(option.valor) is type(value)


def test_json_schema_lists_all_five_item_types():
    schema = Questionnaire.model_json_schema()

    assert set(schema["$defs"]["ItemType"]["enum"]) == {
        "escala_likert",
        "seleccion_multiple",
        "verdadero_falso",
        "desarrollo",
        "emparejamiento",
    }


@pytest.mark.parametrize(
    ("definition", "required_fields"),
    [
        (None, {"titulo", "idioma", "total_items", "items"}),
        (
            "Item",
            {"numero", "enunciado", "tipo", "alternativas", "respuesta_correcta"},
        ),
        ("Option", {"valor", "texto"}),
    ],
    ids=["questionnaire", "item", "option"],
)
def test_json_schema_lists_required_fields(definition, required_fields):
    schema = Questionnaire.model_json_schema()
    model_schema = schema if definition is None else schema["$defs"][definition]

    assert set(model_schema["required"]) == required_fields
