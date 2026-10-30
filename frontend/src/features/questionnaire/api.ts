import type { Questionnaire } from "./types";

export const UPLOAD_PATH = "/upload";
const PROCESSING_ERROR = "Could not process this file. Please try again.";

export async function extractQuestionnaire(
  file: File,
  baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
): Promise<Questionnaire> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${baseUrl.replace(/\/+$/, "")}${UPLOAD_PATH}`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error("Could not reach the server. Please check your connection and try again.");
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new Error(PROCESSING_ERROR);
  }

  if (!response.ok) {
    const detail = body && typeof body === "object" && "detail" in body ? body.detail : null;
    let message = "";
    if (typeof detail === "string") {
      message = detail.trim();
    } else if (Array.isArray(detail)) {
      message = detail
        .map((entry: unknown) =>
          entry && typeof entry === "object" && "msg" in entry && typeof entry.msg === "string"
            ? entry.msg.trim()
            : "",
        )
        .filter(Boolean)
        .join("; ");
    }
    throw new Error(message || PROCESSING_ERROR);
  }

  return body as Questionnaire;
}
