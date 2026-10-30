import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Questionnaire Extractor",
  description: "Extract questionnaire items from PDF, DOCX, or XLSX files and download them as JSON.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full bg-zinc-50 font-sans text-zinc-900">{children}</body>
    </html>
  );
}
