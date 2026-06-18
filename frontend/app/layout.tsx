import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Learning Chatbot",
  description: "Minimal full-stack chatbot with auth, RAG, web search, voice, and vision"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

