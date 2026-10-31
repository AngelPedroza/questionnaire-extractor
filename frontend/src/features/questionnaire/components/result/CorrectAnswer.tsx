import type { QuestionnaireItem } from "../../types";

interface CorrectAnswerProps {
  answer: QuestionnaireItem["respuesta_correcta"];
}

export default function CorrectAnswer({ answer }: CorrectAnswerProps) {
  if (answer === null) return null;

  return (
    <strong className="block rounded bg-zinc-100 p-3 text-sm">
      Correct answer: {answer}
    </strong>
  );
}
