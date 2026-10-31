import type { QuestionnaireOption } from "../../types";

interface ItemOptionsProps {
  options: QuestionnaireOption[];
}

export default function ItemOptions({ options }: ItemOptionsProps) {
  if (options.length === 0) return null;

  return (
    <ul className="space-y-1">
      {options.map((option, index) => (
        <li key={index}>
          {option.valor} — {option.texto}
        </li>
      ))}
    </ul>
  );
}
