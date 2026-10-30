export type QuestionnaireItemType =
  | "escala_likert"
  | "seleccion_multiple"
  | "verdadero_falso"
  | "desarrollo"
  | "emparejamiento";

export interface QuestionnaireOption {
  valor: number | string;
  texto: string;
}

export interface QuestionnaireItem {
  numero: number;
  enunciado: string;
  tipo: QuestionnaireItemType;
  alternativas: QuestionnaireOption[];
  respuesta_correcta: number | string | null;
}

export interface Questionnaire {
  titulo: string;
  idioma: string;
  total_items: number;
  items: QuestionnaireItem[];
}
