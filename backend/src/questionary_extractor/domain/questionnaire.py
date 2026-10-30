from enum import StrEnum

from pydantic import BaseModel


class ItemType(StrEnum):
    escala_likert = "escala_likert"
    seleccion_multiple = "seleccion_multiple"
    verdadero_falso = "verdadero_falso"
    desarrollo = "desarrollo"
    emparejamiento = "emparejamiento"


class Option(BaseModel):
    valor: str | int
    texto: str


class Item(BaseModel):
    numero: int
    enunciado: str
    tipo: ItemType
    alternativas: list[Option]
    respuesta_correcta: str | int | None


class Questionnaire(BaseModel):
    titulo: str
    idioma: str
    total_items: int
    items: list[Item]
