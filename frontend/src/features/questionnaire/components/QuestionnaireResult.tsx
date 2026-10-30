import type { Questionnaire, QuestionnaireItemType } from "../types";

const typeLabels: Record<QuestionnaireItemType, string> = {
  escala_likert: "Likert scale",
  seleccion_multiple: "Multiple choice",
  verdadero_falso: "True / false",
  desarrollo: "Open-ended",
  emparejamiento: "Matching",
};

interface QuestionnaireResultProps {
  result: Questionnaire;
  fileName: string;
}

export default function QuestionnaireResult({
  result,
  fileName,
}: QuestionnaireResultProps) {
  const json = JSON.stringify(result, null, 2);

  function downloadJson() {
    const url = URL.createObjectURL(new Blob([json], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${fileName.replace(/\.[^.]+$/, "")}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  return (
    <section aria-labelledby="result-title" className="min-w-0 space-y-5">
      <header className="space-y-2">
        <h2 id="result-title" className="wrap-anywhere text-2xl font-semibold">
          {result.titulo}
        </h2>
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-zinc-600">
          <p>Language: {result.idioma}</p>
          <p>Total items: {result.total_items}</p>
        </div>
      </header>
      <ol className="space-y-4">
        {result.items.map((item) => (
          <li
            key={item.numero}
            className="space-y-3 rounded-lg border border-zinc-300 bg-white p-5 wrap-anywhere"
          >
            <h3 className="font-semibold">
              {item.numero}. {item.enunciado}
            </h3>
            <p className="text-sm text-zinc-600">{typeLabels[item.tipo]}</p>
            {item.alternativas.length > 0 && (
              <ul className="space-y-1">
                {item.alternativas.map((option, index) => (
                  <li key={index}>
                    {option.valor} — {option.texto}
                  </li>
                ))}
              </ul>
            )}
            {item.respuesta_correcta !== null && (
              <strong className="block rounded bg-zinc-100 p-3 text-sm">
                Correct answer: {item.respuesta_correcta}
              </strong>
            )}
          </li>
        ))}
      </ol>
      <details className="rounded-lg border border-zinc-300 bg-white p-4">
        <summary className="cursor-pointer font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700">
          Show raw JSON
        </summary>
        <pre
          className="mt-4 max-h-96 overflow-auto rounded bg-zinc-100 p-4 text-xs"
          tabIndex={0}
          aria-label="Raw questionnaire JSON"
        >
          {json}
        </pre>
      </details>
      <button
        type="button"
        onClick={downloadJson}
        className="w-full rounded border border-zinc-400 bg-white px-4 py-2 font-medium hover:bg-zinc-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 sm:w-auto"
      >
        Download JSON
      </button>
    </section>
  );
}
