import { describe, expect, it } from "vitest";
import { validateQuestionnaireFile } from "./file-validation";

describe("validateQuestionnaireFile", () => {
  it.each(["pdf", "docx", "xlsx", "PDF", "DOCX", "XLSX"])(
    "accepts .%s files",
    (extension) => {
      expect(validateQuestionnaireFile(new File(["content"], `survey.${extension}`))).toBeNull();
    },
  );

  it.each(["doc", "txt"])("rejects .%s files", (extension) => {
    expect(validateQuestionnaireFile(new File(["content"], `survey.${extension}`))).toBe(
      "Please choose a PDF, DOCX, or XLSX file.",
    );
  });

  it("rejects empty files", () => {
    expect(validateQuestionnaireFile(new File([], "survey.pdf"))).toBe(
      "The file is empty. Please choose a file with content.",
    );
  });

  it("accepts files exactly 4 MB", () => {
    const file = new File([new Uint8Array(4 * 1024 * 1024)], "survey.pdf");
    expect(validateQuestionnaireFile(file)).toBeNull();
  });

  it("rejects files larger than 4 MB", () => {
    const file = new File([new Uint8Array(4 * 1024 * 1024 + 1)], "survey.pdf");
    expect(validateQuestionnaireFile(file)).toBe("The file must be 4 MB or smaller.");
  });
});
