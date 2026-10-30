interface UploadFormProps {
  canExtract: boolean;
  loading: boolean;
  onFileChange: (file: File | null) => void;
  onExtract: () => void;
}

export default function UploadForm({
  canExtract,
  loading,
  onFileChange,
  onExtract,
}: UploadFormProps) {
  return (
    <form
      className="space-y-4 rounded-lg border border-zinc-300 bg-white p-5"
      onSubmit={(event) => {
        event.preventDefault();
        onExtract();
      }}
    >
      <div className="space-y-2">
        <label htmlFor="questionnaire-file" className="block font-medium">
          Questionnaire file
        </label>
        <input
          id="questionnaire-file"
          type="file"
          accept=".pdf,.docx,.xlsx"
          aria-describedby="file-help"
          disabled={loading}
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
          className="block w-full min-w-0 rounded border border-zinc-300 p-2 text-sm file:mr-3 file:rounded file:bg-zinc-100 file:px-3 file:py-2 file:font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 disabled:opacity-50"
        />
        <p id="file-help" className="text-sm text-zinc-600">
          PDF, DOCX, or XLSX. Maximum file size: 4 MB.
        </p>
      </div>
      <button
        type="submit"
        disabled={!canExtract || loading}
        className="w-full rounded bg-zinc-900 px-4 py-2 font-medium text-white hover:bg-zinc-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
      >
        {loading ? "Extracting…" : "Extract"}
      </button>
      <p role="status" aria-live="polite" className="text-sm text-zinc-600">
        {loading ? "Extracting your questionnaire. Please wait." : ""}
      </p>
    </form>
  );
}
