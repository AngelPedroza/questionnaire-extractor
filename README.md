# Questionnaire Extractor

> Upload a questionnaire as PDF, DOCX or XLSX and get its items, answer options and correct answers as standardized JSON.

Psychometric questionnaires often live in PDF, Word or Excel files, and loading them into a digital platform by hand takes hours. This app reads the document, detects each item, its type and its options with an LLM, and returns a JSON that follows one fixed schema. Documents in Italian, Spanish and English are supported.

**Live demo:** _pending deployment_

## How it works

```
Next.js UI ──POST /upload──▶ FastAPI
                               ├─ 1. validate the file by its bytes (signature + size)
                               ├─ 2. extract plain text (pdfplumber / python-docx / openpyxl)
                               ├─ 3. LLM with a JSON schema (Ollama locally, Gemini in production)
                               └─ 4. post-process (no items → error, total_items = len(items))
```

## Output format

```json
{
  "titulo": "Questionario di esempio",
  "idioma": "it",
  "total_items": 2,
  "items": [
    {
      "numero": 1,
      "enunciado": "Mi preoccupo eccessivamente per cose di poca importanza.",
      "tipo": "escala_likert",
      "alternativas": [
        { "valor": 0, "texto": "Mai" },
        { "valor": 1, "texto": "A volte" }
      ],
      "respuesta_correcta": null
    },
    {
      "numero": 2,
      "enunciado": "Quale numero completa la serie: 2, 4, 8, 16, ...?",
      "tipo": "seleccion_multiple",
      "alternativas": [
        { "valor": "A", "texto": "18" },
        { "valor": "C", "texto": "32" }
      ],
      "respuesta_correcta": "C"
    }
  ]
}
```

`tipo` is one of `escala_likert`, `seleccion_multiple`, `verdadero_falso`, `desarrollo`, `emparejamiento`.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Vitest |
| Backend | Python 3.13, FastAPI, Pydantic, pydantic-settings, uv, Pytest, Ruff |
| File parsing | pdfplumber, python-docx, openpyxl |
| LLM | Ollama + `qwen3.5:9b` (local), Google Gemini free tier (production) |

## Getting started

### Prerequisites

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- Node.js 24 and [pnpm](https://pnpm.io/) 10
- [Ollama](https://ollama.com/download) running locally, with the model pulled:

```bash
ollama pull qwen3.5:9b
```

### Backend

```bash
cd backend
uv sync
cp .env.example .env
uv run uvicorn questionary_extractor.main:app --reload --port 8000
```

API docs are served at <http://localhost:8000/docs>.

### Frontend

```bash
cd frontend
pnpm install
cp .env.example .env.local
pnpm dev
```

Open <http://localhost:3000>, choose a file from [`data/`](data/) and press **Extract**.

## Environment variables

### Backend (`backend/.env`)

| Name | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` for local development, `gemini` for production |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen3.5:9b` | Local model used for extraction |
| `GEMINI_API_KEY` | — | Required when `LLM_PROVIDER=gemini`. Get one at [Google AI Studio](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | `gemini-flash-latest` | Gemini model used for extraction |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON list of allowed frontend origins |

### Frontend (`frontend/.env.local`)

| Name | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL. Embedded at build time |

API keys go in environment variables only; `.env` files are git-ignored.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check, returns `{"status": "ok"}` |
| `POST` | `/upload` | Multipart form with a `file` field. Returns the questionnaire JSON |

Errors are returned as `{"detail": "<message>"}`:

| Status | When |
|---|---|
| `413` | The file is larger than 4 MB |
| `415` | Unsupported, corrupted or disguised file (e.g. a PDF renamed to `.docx`) |
| `422` | No text could be extracted or no questionnaire items were detected |
| `502` | The LLM returned an invalid response |
| `503` | The LLM is not reachable |

## Testing

```bash
cd backend && uv run pytest
cd frontend && pnpm test
```

## Project structure

```
backend/src/questionary_extractor/
├── domain/        # questionnaire model, domain errors, file type validation
├── application/   # ExtractQuestionnaire use case
├── adapters/      # file readers, shared prompt, QuestionnaireLLM ABC + Ollama/Gemini adapters
├── api/           # routes and domain error → HTTP mapping
├── config.py      # settings from environment variables
└── main.py        # FastAPI app, CORS, error handler
frontend/src/features/questionnaire/  # upload form, result view, API client
data/              # sample questionnaires (public domain or original), see data/README.md
```

A Zed debug configuration for the backend lives in `.zed/debug.json`.

## Assumptions and decisions

- **File validation by content, not by name.** PDFs are recognized by the `%PDF-` signature and DOCX/XLSX by the main content type declared in `[Content_Types].xml`. The extension must match the real type. This uses only the standard library, so it runs on serverless platforms without system libraries such as libmagic.
- **4 MB upload limit**, because Vercel Functions reject request bodies above 4.5 MB. Archives that expand beyond 50 MB are rejected as possible zip bombs.
- **Scanned PDFs are not supported.** Without OCR, an image-only PDF yields no text and returns `422`.
- **`total_items` is computed by the backend** from the extracted items instead of trusting the LLM.
- **`respuesta_correcta` is filled only when the document states it** (answer key, inline answer or answer column); otherwise it is `null`.
- **Matching questions:** each left-column element is one item and the right-column choices are its `alternativas`.
- **Likert values** use the number shown in the document, or the option order starting at 1.
- **`idioma`** is the ISO 639-1 code of the document language.
- **Local model: `qwen3.5:9b`.** Among models that fit an 18 GB laptop, it reports the strongest instruction following (IFEval 91.5) and multilingual scores (MMLU-ProX 76.3) on its [model card](https://huggingface.co/Qwen/Qwen3.5-9B). Extraction runs with `think=False` and temperature 0.
- **Production LLM: Gemini.** The [Ollama docs](https://docs.ollama.com/capabilities/structured-outputs) state that Ollama Cloud does not support structured outputs, while Gemini enforces the JSON schema (`response_json_schema`). Both adapters share the same Pydantic schema and prompt.
- **Sample data** contains only public-domain instruments (IPIP, GAD-7, Rosenberg) or original items; see [`data/README.md`](data/README.md).
