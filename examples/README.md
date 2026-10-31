# Sample questionnaires

Test documents for the questionnaire extractor. All content is public domain or original.
Each document has the JSON returned by `POST /upload` next to it, with the same name and a `.json`
extension (for `07`, the error response).

| File | Instrument | Lang | Item types | Correct answer | Source / license |
|---|---|---|---|---|---|
| `01_mini-ipip_big-five_en.pdf` | Mini-IPIP (Big Five), 20 items | en | Likert 1–5 | — | IPIP, public domain |
| `02_gad-7_ansiedad_es.docx` | GAD-7 (anxiety), 7 + 1 items | es | Likert 0–3, single choice | — | Pfizer, no permission required |
| `03_autostima-rosenberg_it.xlsx` | Rosenberg Self-Esteem, 10 items | it | Likert 4 points | — | Public domain (UMD); working translation |
| `04_razonamiento-logico_es.pdf` | Logical reasoning, 13 items | es | Multiple choice, open | Answer key on last page | Original + adapted CRT (Frederick, 2005) |
| `05_conoscenza-emozioni_it.docx` | Emotion knowledge, 13 items | it | True/false, matching, open | Inline after each item | Original |
| `06_situational-judgment_work-style_en.xlsx` | SJT + work style, 11 items (2 sheets) | en | Multiple choice, true/false | "Best response" column (sheet 1 only) | Original |
| `07_sin-items_circular_es.docx` | Internal memo | es | None | — | Original — negative case, expect "no items detected" |
