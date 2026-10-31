import type { Questionnaire } from "../../types";
import DownloadJsonButton from "./DownloadJsonButton";

interface ResultHeaderProps {
  result: Questionnaire;
  json: string;
  fileName: string;
}

export default function ResultHeader({ result, json, fileName }: ResultHeaderProps) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 space-y-2">
        <h2 id="result-title" className="wrap-anywhere text-2xl font-semibold">
          {result.titulo}
        </h2>
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-zinc-600">
          <p>Language: {result.idioma}</p>
          <p>Total items: {result.total_items}</p>
        </div>
      </div>
      <DownloadJsonButton json={json} fileName={fileName} />
    </header>
  );
}
