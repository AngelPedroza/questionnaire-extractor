from fastapi.testclient import TestClient

from questionary_extractor.domain.questionnaire import Questionnaire


def recording_extractor(calls):
    def extract(filename, content):
        calls.append((filename, content))
        return Questionnaire(titulo="Sample", idioma="es", total_items=0, items=[])

    return extract


def test_upload_rejects_more_than_one_file_without_processing(monkeypatch):
    from questionary_extractor.api import routes
    from questionary_extractor.main import app

    calls = []
    monkeypatch.setattr(routes, "extractor", recording_extractor(calls))
    with TestClient(app) as client:
        response = client.post(
            "/upload",
            files=[
                ("file", ("first.pdf", b"%PDF-1.7 first", "application/pdf")),
                ("file", ("second.pdf", b"%PDF-1.7 second", "application/pdf")),
            ],
            headers={"Origin": "http://localhost:3000"},
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "Send exactly one file per request."}
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert calls == []


def test_upload_processes_a_single_file(monkeypatch):
    from questionary_extractor.api import routes
    from questionary_extractor.main import app

    calls = []
    monkeypatch.setattr(routes, "extractor", recording_extractor(calls))
    with TestClient(app) as client:
        response = client.post(
            "/upload",
            files={"file": ("only.pdf", b"%PDF-1.7 only", "application/pdf")},
        )

    assert response.status_code == 200
    assert calls == [("only.pdf", b"%PDF-1.7 only")]
