export default function HowItWorks() {
  return (
    <section aria-labelledby="how-it-works-title" className="space-y-2 pt-3">
      <h2 id="how-it-works-title" className="font-semibold">
        How it works
      </h2>
      <ol className="list-decimal space-y-1 pl-5 text-sm text-zinc-600">
        <li>
          Choose one questionnaire file: PDF, DOCX or XLSX, up to 4 MB. Only one file per extraction.
        </li>
        <li>Press Extract. Processing usually takes 30–60 seconds.</li>
        <li>Review the extracted items below and download the JSON.</li>
      </ol>
    </section>
  );
}
