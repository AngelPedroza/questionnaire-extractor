export function validateQuestionnaireFile(file: File): string | null {
  if (!/\.(pdf|docx|xlsx)$/i.test(file.name)) {
    return "Please choose a PDF, DOCX, or XLSX file.";
  }
  if (file.size === 0) {
    return "The file is empty. Please choose a file with content.";
  }
  // Vercel Functions reject request bodies above 4.5 MB.
  if (file.size > 4 * 1024 * 1024) {
    return "The file must be 4 MB or smaller.";
  }
  return null;
}
