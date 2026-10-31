interface RawJsonPanelProps {
  json: string;
}

export default function RawJsonPanel({ json }: RawJsonPanelProps) {
  return (
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
  );
}
