import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from questionary_extractor.api.errors import questionnaire_error_handler
from questionary_extractor.api.routes import router
from questionary_extractor.config import settings
from questionary_extractor.domain.errors import QuestionnaireError

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Questionnaire Extractor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(QuestionnaireError, questionnaire_error_handler)
app.include_router(router)
