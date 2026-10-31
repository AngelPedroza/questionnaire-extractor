interface DownloadJsonButtonProps {
  json: string;
  fileName: string;
}

export default function DownloadJsonButton({ json, fileName }: DownloadJsonButtonProps) {
  function downloadJson() {
    const url = URL.createObjectURL(new Blob([json], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${fileName.replace(/\.[^.]+$/, "")}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  return (
    <button
      type="button"
      onClick={downloadJson}
      className="w-full shrink-0 rounded border border-zinc-400 bg-white px-4 py-2 font-medium hover:bg-zinc-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 sm:w-auto"
    >
      Download JSON
    </button>
  );
}
