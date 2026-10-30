# Questionnaire Extractor

Upload a PDF, DOCX, or XLSX questionnaire (up to 4 MB), review extracted items, and download the result as JSON. See the [root README](../README.md) for the full project setup.

## Run locally

With dependencies already installed:

```sh
cp .env.example .env.local
pnpm dev
```

Open `http://localhost:3000`. The browser uploads the file directly to the API configured by `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`. The API must allow requests from the frontend origin.

The upload path is defined once as `UPLOAD_PATH` in `src/features/questionnaire/api.ts`. Requests use multipart form data with the field `file`.

`NEXT_PUBLIC_API_URL` is embedded at build time. Set it before building for deployment.

## Verify

```sh
pnpm test
pnpm lint
pnpm build
```

Tests mock the API or fetch; they do not require a running backend. The UI uses system fonts and has no external font dependency.
