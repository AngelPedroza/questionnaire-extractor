import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import Page from "./page";
import { metadata } from "./layout";

afterEach(cleanup);

it("renders the questionnaire extractor on the home page", () => {
  render(<Page />);
  expect(screen.getByRole("heading", { name: "Questionnaire Extractor", level: 1 })).toBeDefined();
  expect(screen.getByLabelText("Questionnaire file")).toBeDefined();
});

it("describes the questionnaire app in its metadata", () => {
  expect(metadata.title).toBe("Questionnaire Extractor");
  expect(metadata.description).toBe("Extract questionnaire items from PDF, DOCX, or XLSX files and download them as JSON.");
});
