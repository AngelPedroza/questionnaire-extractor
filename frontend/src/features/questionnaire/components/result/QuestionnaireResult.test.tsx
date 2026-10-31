import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Questionnaire, QuestionnaireItemType } from "../../types";
import QuestionnaireResult from "./QuestionnaireResult";

const result: Questionnaire = {
  titulo: "Learning survey",
  idioma: "en",
  total_items: 1,
  items: [{
    numero: 3,
    enunciado: "I enjoy learning.",
    tipo: "escala_likert",
    alternativas: [{ valor: 0, texto: "Never" }, { valor: "A", texto: "Always" }],
    respuesta_correcta: 0,
  }],
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("QuestionnaireResult", () => {
  it("shows the summary, item number and options", () => {
    render(<QuestionnaireResult result={result} fileName="survey.pdf" />);
    expect(screen.getByText("Language: en")).toBeDefined();
    expect(screen.getByText("Total items: 1")).toBeDefined();
    expect(screen.getByRole("heading", { name: "3. I enjoy learning." })).toBeDefined();
    expect(screen.getByText("0 — Never")).toBeDefined();
    expect(screen.getByText("A — Always")).toBeDefined();
  });

  it.each<[QuestionnaireItemType, string]>([
    ["escala_likert", "Likert scale"],
    ["seleccion_multiple", "Multiple choice"],
    ["verdadero_falso", "True / false"],
    ["desarrollo", "Open-ended"],
    ["emparejamiento", "Matching"],
  ])("labels %s in English", (tipo, label) => {
    render(<QuestionnaireResult
      result={{ ...result, items: [{ ...result.items[0], tipo }] }}
      fileName="survey.pdf"
    />);
    expect(screen.getByText(label)).toBeDefined();
  });

  it.each([0, "A"])("highlights the non-null correct answer %s", (answer) => {
    render(<QuestionnaireResult
      result={{ ...result, items: [{ ...result.items[0], respuesta_correcta: answer }] }}
      fileName="survey.pdf"
    />);
    expect(screen.getByText(`Correct answer: ${answer}`).tagName).toBe("STRONG");
  });

  it("toggles the raw JSON preview", async () => {
    const user = userEvent.setup();
    render(<QuestionnaireResult result={result} fileName="survey.pdf" />);
    const toggle = screen.getByText("Show raw JSON");
    const details = toggle.closest("details")!;
    expect(details.open).toBe(false);
    await user.click(toggle);
    expect(details.open).toBe(true);
    expect(details.querySelector("pre")?.textContent).toBe(JSON.stringify(result, null, 2));
    await user.click(toggle);
    expect(details.open).toBe(false);
  });

  it("omits the correct answer when it is null", () => {
    render(<QuestionnaireResult
      result={{ ...result, items: [{ ...result.items[0], respuesta_correcta: null }] }}
      fileName="survey.pdf"
    />);
    expect(screen.queryByText(/Correct answer:/)).toBeNull();
  });

  it("downloads JSON using the original filename and revokes the object URL", async () => {
    const user = userEvent.setup();
    const createObjectURL = vi.fn().mockReturnValue("blob:questionnaire");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    let downloadedName = "";
    let downloadedUrl = "";
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      downloadedName = this.download;
      downloadedUrl = this.href;
    });
    render(<QuestionnaireResult result={result} fileName="my.survey.PDF" />);
    await user.click(screen.getByRole("button", { name: "Download JSON" }));
    expect(downloadedName).toBe("my.survey.json");
    expect(downloadedUrl).toBe("blob:questionnaire");
    const blob: Blob = createObjectURL.mock.calls[0][0];
    expect(blob.type).toBe("application/json");
    const content = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsText(blob);
    });
    expect(content).toBe(JSON.stringify(result, null, 2));
    await waitFor(() => expect(revokeObjectURL).toHaveBeenCalledWith("blob:questionnaire"));
    expect(document.querySelector("a[download]")).toBeNull();
  });
});
