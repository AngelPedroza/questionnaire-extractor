import json

from questionary_extractor.domain.questionnaire import Questionnaire

SYSTEM_PROMPT = f"""Extract the questionnaire items from the document text given by the user.

General rules:
- Copy statements and option texts verbatim, in the document language.
- idioma: ISO 639-1 code of the document language.
- numero: the item number shown in the document.
- If the document contains no questionnaire items, return an empty items list.

Item types (tipo):
- escala_likert: a statement rated on an ordered scale shared by several items
  (agreement, frequency, accuracy or intensity). It has no correct answer.
- seleccion_multiple: a question with listed options where one option is chosen.
- verdadero_falso: a statement answered as true or false, in any language; its
  alternativas are the two options shown (for example Vero/Falso or True/False).
- desarrollo: an open question answered in free text; alternativas is an empty list.
- emparejamiento: matching; each left-column element is one item, and its
  alternativas are ALL the right-column choices (the same full list for every item).

alternativas:
- valor is the label shown for the option (letter, number or word). If a scale shows
  no numbers, use the order starting at 1.

respuesta_correcta (only when the document states it in an answer key, an inline
answer or an answer column; otherwise null):
- For items with alternativas, it must be exactly the valor of the correct
  alternative, never its position.
- For desarrollo items, copy the answer text from the answer key.
- escala_likert items always have null.

Return ONLY JSON matching this schema:
{json.dumps(Questionnaire.model_json_schema())}
"""
