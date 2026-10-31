import type { Questionnaire } from "../../types";
import ItemCard from "./ItemCard";
import RawJsonPanel from "./RawJsonPanel";
import ResultHeader from "./ResultHeader";

interface QuestionnaireResultProps {
  result: Questionnaire;
  fileName: string;
}

export default function QuestionnaireResult({
  result,
  fileName,
}: QuestionnaireResultProps) {
  const json = JSON.stringify(result, null, 2);

  return (
    <section aria-labelledby="result-title" className="min-w-0 space-y-5">
      <ResultHeader result={result} json={json} fileName={fileName} />
      <ol className="space-y-4">
        {result.items.map((item) => (
          <li key={item.numero}>
            <ItemCard item={item} />
          </li>
        ))}
      </ol>
      <RawJsonPanel json={json} />
    </section>
  );
}
