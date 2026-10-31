import type { QuestionnaireItemType } from "../../types";

const typeLabels: Record<QuestionnaireItemType, string> = {
  escala_likert: "Likert scale",
  seleccion_multiple: "Multiple choice",
  verdadero_falso: "True / false",
  desarrollo: "Open-ended",
  emparejamiento: "Matching",
};

interface ItemTypeBadgeProps {
  type: QuestionnaireItemType;
}

export default function ItemTypeBadge({ type }: ItemTypeBadgeProps) {
  return (
    <span className="ml-2 inline-block rounded bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-600">
      {typeLabels[type]}
    </span>
  );
}
