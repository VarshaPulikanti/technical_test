import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Creator Compare — RAG",
  description: "Compare YouTube vs Instagram engagement with transcript RAG",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
