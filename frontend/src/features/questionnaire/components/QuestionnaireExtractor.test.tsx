import { act, cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { extractQuestionnaire } from "../api";
import type { Questionnaire } from "../types";
import QuestionnaireExtractor from "./QuestionnaireExtractor";

vi.mock("../api", () => ({ extractQuestionnaire: vi.fn() }));
const extractMock = vi.mocked(extractQuestionnaire);
const result: Questionnaire = {
  titulo: "Learning survey",
  idioma: "en",
  total_items: 2,
  items: [
    { numero: 1, enunciado: "Do you enjoy learning?", tipo: "verdadero_falso", alternativas: [], respuesta_correcta: null },
    { numero: 2, enunciado: "Describe your goals.", tipo: "desarrollo", alternativas: [], respuesta_correcta: null },
  ],
};

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

function setup() {
  const user = userEvent.setup({ applyAccept: false });
  render(<QuestionnaireExtractor />);
  const input = screen.getByLabelText<HTMLInputElement>("Questionnaire file");
  const button = screen.getByRole<HTMLButtonElement>("button", { name: "Extract" });
  return { user, input, button };
}

async function submitFile() {
  const controls = setup();
  const file = new File(["content"], "survey.pdf");
  await controls.user.upload(controls.input, file);
  await controls.user.click(controls.button);
  return { ...controls, file };
}

describe("QuestionnaireExtractor", () => {
  it("keeps extraction disabled until a valid file is selected", () => {
    const { input, button } = setup();
    expect(input.accept).toBe(".pdf,.docx,.xlsx");
    expect(button.disabled).toBe(true);
  });

  it("shows the validation error and disables extraction for an invalid file", async () => {
    const { user, input, button } = setup();
    await user.upload(input, new File(["content"], "survey.txt"));
    expect(screen.getByRole("alert").textContent).toBe("Please choose a PDF, DOCX, or XLSX file.");
    expect(button.disabled).toBe(true);
    expect(extractMock).not.toHaveBeenCalled();
  });

  it("displays the extracted title and item statements", async () => {
    extractMock.mockResolvedValue(result);
    const { file } = await submitFile();
    expect(extractMock).toHaveBeenCalledWith(file);
    expect(await screen.findByRole("heading", { name: result.titulo })).toBeDefined();
    for (const item of result.items) {
      expect(screen.getByRole("heading", { name: `${item.numero}. ${item.enunciado}` })).toBeDefined();
    }
  });

  it("shows API rejection in an alert", async () => {
    extractMock.mockRejectedValue(new Error("This file could not be read."));
    const { button } = await submitFile();
    expect((await screen.findByRole("alert")).textContent).toBe("This file could not be read.");
    expect(button.disabled).toBe(false);
  });

  it.each([
    { ...result, total_items: 0, items: [] },
    { ...result, total_items: 0 },
    { ...result, items: [] },
  ])("reports when no items are detected: %j", async (emptyResult) => {
    extractMock.mockResolvedValue(emptyResult);
    await submitFile();
    expect((await screen.findByRole("alert")).textContent).toBe("No items were detected in this file.");
    expect(screen.queryByRole("heading", { name: result.titulo })).toBeNull();
  });

  it("announces loading and prevents changing files or resubmitting", async () => {
    const pending = Promise.withResolvers<Questionnaire>();
    extractMock.mockReturnValue(pending.promise);
    const { input, button } = await submitFile();
    expect(button.disabled).toBe(true);
    expect(input.disabled).toBe(true);
    expect(screen.getByRole("status").getAttribute("aria-live")).toBe("polite");
    expect(screen.getByRole("status").textContent).toContain("Extracting");
    await act(async () => pending.resolve(result));
    expect(input.disabled).toBe(false);
    expect(button.disabled).toBe(false);
  });

  it("clears the previous result when another file is selected", async () => {
    extractMock.mockResolvedValue(result);
    const { user, input, button } = await submitFile();
    await screen.findByRole("heading", { name: result.titulo });
    await user.upload(input, new File(["new content"], "new.docx"));
    expect(screen.queryByRole("heading", { name: result.titulo })).toBeNull();
    expect(button.disabled).toBe(false);
  });
});
