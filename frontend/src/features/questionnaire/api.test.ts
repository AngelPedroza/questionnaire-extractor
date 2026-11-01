import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { extractQuestionnaire } from "./api";

const questionnaire = {
  titulo: "Sample questionnaire",
  idioma: "en",
  total_items: 1,
  items: [{
    numero: 1,
    enunciado: "How are you?",
    tipo: "desarrollo",
    alternativas: [],
    respuesta_correcta: null,
  }],
};
const file = new File(["content"], "survey.pdf");
const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockResolvedValue(Response.json(questionnaire));
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.resetAllMocks();
});

describe("extractQuestionnaire", () => {
  it("posts the file as FormData to the upload endpoint", async () => {
    await extractQuestionnaire(file, "https://api.example.test");
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("https://api.example.test/upload");
    expect(options?.method).toBe("POST");
    expect(options?.body).toBeInstanceOf(FormData);
    expect((options?.body as FormData).get("file")).toBe(file);
    expect(options?.headers).toBeUndefined();
  });

  it("returns parsed JSON on success", async () => {
    await expect(extractQuestionnaire(file)).resolves.toEqual(questionnaire);
  });

  it("uses localhost when the environment variable is unset", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", undefined);
    await extractQuestionnaire(file);
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/upload");
  });

  it("uses NEXT_PUBLIC_API_URL when configured", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://configured.example.test");
    await extractQuestionnaire(file);
    expect(fetchMock.mock.calls[0][0]).toBe("https://configured.example.test/upload");
  });

  it("avoids a duplicate slash for a trailing-slash base URL", async () => {
    await extractQuestionnaire(file, "https://api.example.test/");
    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example.test/upload");
  });

  it("throws the backend string detail", async () => {
    fetchMock.mockResolvedValue(Response.json({ detail: "Invalid document format." }, { status: 400 }));
    await expect(extractQuestionnaire(file)).rejects.toThrow("Invalid document format.");
  });

  it("joins validation detail messages for 422", async () => {
    fetchMock.mockResolvedValue(Response.json({
      detail: [{ msg: "File is required", loc: ["body", "file"] }, { msg: "Invalid upload" }],
    }, { status: 422 }));
    await expect(extractQuestionnaire(file)).rejects.toThrow("File is required; Invalid upload");
  });

  it.each([{}, { detail: "" }, { detail: [] }, { detail: [{ other: "missing" }] }])(
    "uses a generic error when detail is unavailable: %j",
    async (body) => {
      fetchMock.mockResolvedValue(Response.json(body, { status: 500 }));
      await expect(extractQuestionnaire(file)).rejects.toThrow("Could not process this file. Please try again.");
    },
  );

  it("uses a generic error for a non-JSON response", async () => {
    fetchMock.mockResolvedValue(new Response("server unavailable", { status: 503 }));
    await expect(extractQuestionnaire(file)).rejects.toThrow("Could not process this file. Please try again.");
  });

  it("uses a generic error for malformed success JSON", async () => {
    fetchMock.mockResolvedValue(new Response("not JSON", { status: 200 }));
    await expect(extractQuestionnaire(file)).rejects.toThrow("Could not process this file. Please try again.");
  });

  it("reports network failures in friendly language", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(extractQuestionnaire(file)).rejects.toThrow(
      "Could not reach the server. Check your connection, or wait a few minutes if you sent several files in a row.",
    );
  });
});
