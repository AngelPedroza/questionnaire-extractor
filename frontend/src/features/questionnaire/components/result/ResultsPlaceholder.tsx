export default function ResultsPlaceholder() {
  return (
    <section
      aria-labelledby="results-placeholder-title"
      className="space-y-2 rounded-lg border border-dashed border-zinc-300 bg-white p-5"
    >
      <h2 id="results-placeholder-title" className="font-semibold">
        Results will appear here
      </h2>
      <p className="text-sm text-zinc-600">
        After you press Extract, the questionnaire items will be listed here.
      </p>
    </section>
  );
}
