"use client";

import { useState } from "react";
import { extractQuestionnaire } from "../api";
import { validateQuestionnaireFile } from "../file-validation";
import type { Questionnaire } from "../types";
import QuestionnaireResult from "./QuestionnaireResult";
import UploadForm from "./UploadForm";

type Status = "idle" | "loading" | "success" | "error";

export default function QuestionnaireExtractor() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<Questionnaire | null>(null);
  const [error, setError] = useState<string | null>(null);

  function selectFile(nextFile: File | null) {
    const validationError = nextFile ? validateQuestionnaireFile(nextFile) : null;
    setFile(validationError ? null : nextFile);
    setResult(null);
    setError(validationError);
    setStatus(validationError ? "error" : "idle");
  }

  async function extract() {
    if (!file || status === "loading") return;
    setStatus("loading");
    setError(null);
    setResult(null);
    try {
      const extracted = await extractQuestionnaire(file);
      if (extracted.total_items === 0 || extracted.items.length === 0) {
        throw new Error("No items were detected in this file.");
      }
      setResult(extracted);
      setStatus("success");
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not process this file. Please try again.",
      );
      setStatus("error");
    }
  }

  return (
    <main className="mx-auto w-full max-w-3xl space-y-8 px-4 py-10 sm:px-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Questionnaire Extractor
        </h1>
        <p className="text-zinc-600">
          Upload a questionnaire to view and download its questions as JSON.
        </p>
      </header>
      <UploadForm
        canExtract={file !== null}
        loading={status === "loading"}
        onFileChange={selectFile}
        onExtract={extract}
      />
      {status === "error" && (
        <p role="alert" className="rounded-lg border border-zinc-400 bg-zinc-100 p-4">
          {error}
        </p>
      )}
      {status === "success" && result && file && (
        <QuestionnaireResult result={result} fileName={file.name} />
      )}
    </main>
  );
}
