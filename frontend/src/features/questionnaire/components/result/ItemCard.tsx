import type { QuestionnaireItem } from "../../types";
import CorrectAnswer from "./CorrectAnswer";
import ItemOptions from "./ItemOptions";
import ItemTypeBadge from "./ItemTypeBadge";

interface ItemCardProps {
  item: QuestionnaireItem;
}

export default function ItemCard({ item }: ItemCardProps) {
  return (
    <details className="rounded-lg border border-zinc-300 bg-white wrap-anywhere">
      <summary className="cursor-pointer rounded-lg p-5 font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700">
        {/* A heading inside <summary> is valid HTML and keeps heading navigation for screen readers. */}
        <h3 className="inline">
          {item.numero}. {item.enunciado}
        </h3>
        <ItemTypeBadge type={item.tipo} />
      </summary>
      <div className="space-y-3 px-5 pb-5">
        <ItemOptions options={item.alternativas} />
        <CorrectAnswer answer={item.respuesta_correcta} />
      </div>
    </details>
  );
}
