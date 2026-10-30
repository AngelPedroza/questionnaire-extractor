# Prueba técnica: Backend Developer Python

> **Giunti Psychometrics** · Equipo de Tecnología


| Modalidad         | Plazo de entrega                           |
| ----------------- | ------------------------------------------ |
| Take-home, remoto | Domingo 1 de noviembre a las 9 AM colombia |


---

## 1. El desafío

Giunti Psychometrics está llevando sus cuestionarios y pruebas de evaluación en papel a su plataforma digital de administración y corrección. Hoy ese material existe en PDF, Word o Excel, y cargarlo a mano toma horas.

**Objetivo:** construir una aplicación web que permita **subir un documento** (PDF, Word o Excel) con un cuestionario y **retorne automáticamente** los ítems y sus alternativas de respuesta, estructurados en un **JSON estandarizado**.

---

## 2. Ejemplo de salida esperada

```json
{
  "titulo": "Questionario di esempio",
  "idioma": "it",
  "total_items": 3,
  "items": [
    {
      "numero": 1,
      "enunciado": "Mi preoccupo eccessivamente per cose di poca importanza.",
      "tipo": "escala_likert",
      "alternativas": [
        { "valor": 0, "texto": "Mai" },
        { "valor": 1, "texto": "A volte" },
        { "valor": 2, "texto": "Spesso" },
        { "valor": 3, "texto": "Sempre" }
      ],
      "respuesta_correcta": null
    },
    {
      "numero": 2,
      "enunciado": "Quale numero completa la serie: 2, 4, 8, 16, ...?",
      "tipo": "seleccion_multiple",
      "alternativas": [
        { "valor": "A", "texto": "18" },
        { "valor": "B", "texto": "24" },
        { "valor": "C", "texto": "32" }
      ],
      "respuesta_correcta": "C"
    },
    {
      "numero": 3,
      "enunciado": "Descriva una situazione recente in cui si è sentito sotto pressione.",
      "tipo": "desarrollo",
      "alternativas": [],
      "respuesta_correcta": null
    }
  ]
}
```

---

## 3. Requerimientos


| Área                       | Qué se pide                                                                                                                                                                             |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Subida de archivos**     | Soportar PDF, `.docx` y `.xlsx`.                                                                                                                                                        |
| **Procesamiento**          | Extraer el texto e identificar los ítems, su **tipo** (escala Likert, selección múltiple, verdadero/falso, desarrollo, emparejamiento) y sus alternativas.                              |
| **Respuesta estructurada** | Retornar el JSON según el esquema de arriba. Si la respuesta correcta está indicada en el documento, incluirla. Detectar el idioma del documento (al menos italiano, español e inglés). |
| **Interfaz**               | UI donde el usuario adjunta el archivo, inicia el procesamiento y visualiza o descarga el resultado.                                                                                    |
| **Manejo de errores**      | Informar si no se detectan ítems, si el formato es inválido o si ocurre un error.                                                                                                       |
| **Datos**                  | Usar solo cuestionarios inventados o de dominio público. No subir material de tests comerciales ni datos personales.                                                                    |


---

## 4. Stack


| Capa             | Requerido              | Decisión libre                             |
| ---------------- | ---------------------- | ------------------------------------------ |
| Frontend         | React o Next.js        | Estilos, librerías UI, estado              |
| Backend          | Python · FastAPI       | Estructura, validación, logging            |
| LLM / Extracción | Sin costo (free tier)  | Modelo, proveedor, estrategia de prompting |
| Deploy           | Producción (ver abajo) | Plataforma a elección                      |


**Sobre el LLM:** puedes usar cualquier opción gratuita: Google Gemini (AI Studio), Groq, Mistral, modelos locales con Ollama u otro enfoque sin costo.

> ⚠️ Las API keys van en **variables de entorno**, nunca en el repositorio.

---

## 5. Deploy

- La aplicación debe estar **desplegada y accesible públicamente**.
- Plataforma a elección: Vercel, Render, Railway, Fly.io, etc.
- Incluye la **URL en el README**.

---

## 6. Entregables (checklist)

- [ ] **Repositorio público** en GitHub con historial de commits limpio.
- [ ] **README** con instrucciones de instalación, variables de entorno necesarias y URL del deploy.
- [ ] **Carpeta `/examples`** con al menos un archivo de prueba y el JSON resultante.
- [ ] **Tests** con Pytest para, al menos, la validación del archivo y el esquema de salida.
- [ ] Compartir acceso al repositorio con [**matias@adipa.cl**](mailto:matias@adipa.cl).

---

## 7. Consultas

- Ante cualquier duda de interpretación, **documenta tu supuesto en el README y avanza**.
- Contacto: [**matias.santander@giuntipsy.com**](mailto:matias.santander@giuntipsy.com)
- Asunto: `Prueba Técnica – [Tu nombre]`