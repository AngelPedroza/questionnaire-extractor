import json

from questionary_extractor.domain.questionnaire import Questionnaire

SYSTEM_PROMPT = f"""Extract questionnaire items from the document text given by the user.
Copy statements and options verbatim in the document language.
Set idioma to the ISO 639-1 language code.
Set tipo to one of the enum values in the schema.
For Likert options, use the numeric value shown, otherwise their order starting at 1.
Set respuesta_correcta only when the document states it in an answer key, inline answer,
or answer column; otherwise use null.
Open questions must have an empty alternativas list.
For matching items, each left-column element is one item and the right-column choices
are its alternativas.
If the document contains no questionnaire items, return an empty items list.
Return ONLY JSON matching this schema:
{json.dumps(Questionnaire.model_json_schema())}
"""
