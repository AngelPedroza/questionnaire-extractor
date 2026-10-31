import json
import unicodedata
from pathlib import Path

import pytest

MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
EXPECTED_DIR = Path(__file__).parent / "expected"


def normalize(value):
    # Tolerate typography and spacing differences ("…" vs "...", double spaces, case).
    if isinstance(value, str):
        return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()
    return value


def differences(expected: dict, actual: dict) -> list[str]:
    found = []
    for field in ("titulo", "idioma", "total_items"):
        # A null expected titulo means the document has no overall title to copy.
        if field == "titulo" and expected[field] is None:
            continue
        if normalize(actual[field]) != normalize(expected[field]):
            found.append(
                f"{field}: expected {expected[field]!r}, got {actual[field]!r}"
            )

    actual_items = {item["numero"]: item for item in actual["items"]}
    for item in expected["items"]:
        number = item["numero"]
        got = actual_items.get(number)
        if got is None:
            found.append(f"item {number}: missing")
            continue
        for field in ("enunciado", "tipo", "respuesta_correcta"):
            if normalize(got[field]) != normalize(item[field]):
                found.append(
                    f"item {number} {field}: expected {item[field]!r}, got {got[field]!r}"
                )
        expected_options = [
            (normalize(o["valor"]), normalize(o["texto"])) for o in item["alternativas"]
        ]
        got_options = [
            (normalize(o["valor"]), normalize(o["texto"])) for o in got["alternativas"]
        ]
        if got_options != expected_options:
            found.append(
                f"item {number} alternativas: expected {item['alternativas']!r}, "
                f"got {got['alternativas']!r}"
            )

    extra = sorted(set(actual_items) - {item["numero"] for item in expected["items"]})
    if extra:
        found.append(f"unexpected items: {extra}")
    return found


def upload(client, path):
    with path.open("rb") as document:
        return client.post(
            "/upload",
            files={"file": (path.name, document, MIME_BY_SUFFIX[path.suffix])},
        )


# Each case pairs a document in examples/ with tests/e2e/expected/<same name>.json,
# which holds the exact response body: a questionnaire (200) or an error detail.
@pytest.mark.parametrize(
    ("document", "status_code"),
    [
        ("01_mini-ipip_big-five_en.pdf", 200),
        ("02_gad-7_ansiedad_es.docx", 200),
        ("03_autostima-rosenberg_it.xlsx", 200),
        ("04_razonamiento-logico_es.pdf", 200),
        ("05_conoscenza-emozioni_it.docx", 200),
        ("06_situational-judgment_work-style_en.xlsx", 200),
        ("07_sin-items_circular_es.docx", 422),
    ],
)
def test_upload_returns_expected_response(client, examples_dir, document, status_code):
    expected_file = EXPECTED_DIR / f"{Path(document).stem}.json"
    expected = json.loads(expected_file.read_text(encoding="utf-8"))

    response = upload(client, examples_dir / document)

    assert response.status_code == status_code, response.text
    if status_code != 200:
        assert response.json() == expected
        return
    found = differences(expected, response.json())
    assert not found, "\n".join(found)
