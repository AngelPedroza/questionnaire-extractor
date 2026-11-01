# Questionnaire Extractor

> Upload a questionnaire as PDF, DOCX or XLSX and get its items, answer options and correct answers as standardized JSON.

Psychometric questionnaires often live in PDF, Word or Excel files, and loading them into a digital platform by hand takes hours. This app reads the document, detects each item, its type and its options with an LLM, and returns a JSON that follows one fixed schema. Documents in Italian, Spanish and English are supported.

## Try it

Open **https://questionnaire-extractor.vercel.app** — no login or setup needed.

1. Download a sample file from [`examples/`](examples/) (or use your own questionnaire).
2. Under **Questionnaire file**, choose one PDF, DOCX or XLSX file of up to 4 MB.
3. Press **Extract** and wait a few seconds.
4. Expand any item to see its options and correct answer, then press **Download JSON** (or **Show raw JSON** to read it on the page).

Each IP can extract 10 files every 10 minutes. The JSON produced for every sample is in [`examples/`](examples/) next to its source file.

To call the API directly instead of the UI:

```bash
curl -F "file=@examples/02_gad-7_ansiedad_es.docx" https://questionnaire-extractor-api.vercel.app/upload
```

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
| LLM | Ollama + `qwen3.5:9b` (local), Google Gemini `gemini-3.5-flash` free tier (production) |

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

Open <http://localhost:3000>, choose a file from [`examples/`](examples/) and press **Extract**.

## Environment variables

### Backend (`backend/.env`)

| Name | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` for local development, `gemini` for production |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen3.5:9b` | Local model used for extraction |
| `GEMINI_API_KEY` | — | Required when `LLM_PROVIDER=gemini`. Get one at [Google AI Studio](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Gemini model used for extraction |
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
| `POST` | `/upload` | Multipart form with exactly one file in the `file` field. Returns the questionnaire JSON |

Errors are returned as `{"detail": "<message>"}`:

| Status | When |
|---|---|
| `413` | The file is larger than 4 MB |
| `413` | The document is too long to process. Try a shorter file. (Ollama: over ~16,400 characters) |
| `415` | Unsupported, corrupted or disguised file (e.g. a PDF renamed to `.docx`) |
| `422` | No text could be extracted or no questionnaire items were detected |
| `422` | More than one file was sent: "Send exactly one file per request." |
| `429` | More than 10 uploads from the same IP in 10 minutes (production only). Returned by the Vercel Firewall before the request reaches the API, as plain text without CORS headers, so the browser reports it as a connection error |
| `500` | Something went wrong while processing the file. Please try again. |
| `502` | The LLM returned an invalid response |
| `503` | The LLM is not reachable, or its circuit breaker is temporarily open |
| `504` | The document took too long to process. Try a smaller file. |

### Resilience

- **Timeouts and transient-only retries:** Ollama uses a 180 s timeout and retries connection failures twice, but never retries a read timeout or an HTTP error. Gemini uses a 90 s timeout with at most two attempts for HTTP 429/503, connection failures and timeouts. Its nominal budget is about 185 s including backoff, below Vercel's 300 s limit; HTTP timeouts apply to network phases, not a strict end-to-end deadline.
- **Circuit breaker:** three consecutive infrastructure failures open the circuit for 30 s. Calls fail fast while open; one half-open trial checks recovery. Success closes it, infrastructure failure reopens it, and content errors do not count. State is per process/Vercel instance and resets on cold start.
- **Text budget:** the local Ollama context is deliberately kept at 8,192 tokens to limit memory use (~256 MB of KV cache on top of the 7.6 GB model). Input is capped at ~16,400 characters, computed in `adapters/ollama_llm.py` as `(context − prompt − answer reserve) × 3.5 chars/token`; the ratio is a conservative estimate, not a measured token count. Ollama's default keep-alive (5 minutes) unloads the model when idle, so the first request after a pause also pays the model load time.
- **Error boundary:** unexpected processing errors are logged and return the generic JSON message with CORS headers, without taking down the application.

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
examples/          # sample questionnaires + the JSON each one returns, see examples/README.md
backend/tests/e2e/expected/  # expected extraction results used by the end-to-end tests
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
- **Gemini model: `gemini-3.5-flash`, pinned, with `thinking_level="LOW"`.** Measured on the free tier on 2026-10-31 with the GAD-7 sample: `gemini-flash-latest` (then served by `gemini-3.8-flash`) took 62–78 s per document and returned 503 on 3 of the 7 e2e cases; `gemini-flash-lite-latest` answered in 5 s but corrupted accented characters (`Ningún` → `Ningan`); `gemini-3.5-flash` answered in about 5 s, and the whole e2e suite ran in 37 s without a 503. A fixed version is used instead of a `-latest` alias, so Google cannot swap the model behind the validated prompt. Low thinking mirrors `think=False` locally: copying fields needs little reasoning.
- **Rate limit instead of authentication.** The API has no login so evaluators can use the demo without extra steps, and a key shipped to the browser would be public anyway. To stop a single client from exhausting the Gemini quota, a Vercel WAF rule limits `POST /upload` to 10 requests per IP every 10 minutes and answers `429` beyond that. The rule lives in the Vercel project's Firewall settings, not in the code, so local development is not limited. Limits: counters are per Vercel region, and many distinct IPs could still drain the quota; an access code or user accounts would be the next step.
- **Sample data** contains only public-domain instruments (IPIP, GAD-7, Rosenberg) or original items; see [`examples/README.md`](examples/README.md).

## Future work

- Chunk long documents and merge their extracted items instead of rejecting over-budget input.
- Move long-running extraction to asynchronous jobs with progress/status polling, outside the request timeout budget.
