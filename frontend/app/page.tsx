"use client";

import { useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Start a conversation and I’ll help you organize your ideas, research, and notes.",
    },
  ]);

  async function sendMessage() {
    const text = message.trim();
    if ((!text && !selectedFile) || loading) return;

    const userMessage: Message = {
      role: "user",
      content: selectedFile
        ? `${text ? `${text} ` : ""}[Attached: ${selectedFile.name}]`
        : text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      let responseText = "";

      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const uploadResult = await fetch("http://127.0.0.1:8000/api/upload-pdf", {
          method: "POST",
          body: formData,
        });

        const uploadedData = await uploadResult.json();
        if (!uploadResult.ok || uploadedData.error) {
          throw new Error(uploadedData.error || `PDF upload failed (${uploadResult.status}).`);
        }

        const chunks: string[] = uploadedData.chunks ?? [];
        if (chunks.length === 0) {
          responseText = `Processed ${uploadedData.filename}, but no readable text was found.`;
        } else {
          const preview = chunks[0].slice(0, 500);
          responseText = `Processed ${uploadedData.filename}. Extracted ${uploadedData.total_chunks} text chunks.\n\nPreview:\n${preview}${chunks[0].length > 500 ? "..." : ""}`;
        }
      } else {
        const result = await fetch("http://127.0.0.1:8000/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: text, history: messages }),
        });

        const data = await result.json();
        if (!result.ok) {
          throw new Error(data.detail || `Chat request failed (${result.status}).`);
        }
        responseText = data.response || "No response received.";
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: responseText },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: error instanceof Error
            ? `Request failed: ${error.message}`
            : "The request failed unexpectedly.",
        },
      ]);
    } finally {
      setSelectedFile(null);
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-sky-50 px-4 py-8 text-slate-800">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 flex items-center justify-between gap-4">
          <div>
            <p className="mb-2 text-sm font-medium uppercase tracking-[0.2em] text-sky-600">
              Research Workspace
            </p>
            <h1 className="text-4xl font-bold tracking-tight text-slate-900">
              AI Knowledge & Research Assistant
            </h1>
          </div>

          <button
            onClick={() => {
              setMessages([{
                role: "assistant",
                content: "Start a conversation and I’ll help you organize your ideas, research, and notes.",
              }]);
              setMessage("");
              setSelectedFile(null);
            }}
            disabled={loading}
            className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:shadow-md disabled:opacity-50"
          >
            New chat
          </button>
        </header>

        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/60">
          <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-5 py-4">
            <div>
              <p className="text-sm font-semibold text-slate-900">Conversation</p>
              <p className="text-xs text-slate-500">Ask anything about your research</p>
            </div>
            <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">
              Online
            </span>
          </div>

          <div className="h-[420px] overflow-y-auto bg-gradient-to-b from-white to-slate-50 p-5">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-md rounded-2xl px-4 py-3 text-sm shadow-sm ${
                    msg.role === "user"
                      ? "rounded-br-md bg-sky-600 text-white"
                      : "rounded-bl-md bg-slate-100 text-slate-700"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="max-w-md rounded-2xl rounded-bl-md bg-slate-100 px-4 py-3 text-sm text-slate-600 shadow-sm">
                  AI is thinking...
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-slate-200 bg-white p-4">
            <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center">
              <label className="flex w-fit cursor-pointer items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 shadow-sm transition hover:bg-slate-100">
                <span>Attach PDF</span>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  className="hidden"
                />
              </label>

              {selectedFile && (
                <span className="truncate text-xs text-slate-600">
                  Selected: {selectedFile.name}
                </span>
              )}
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="flex flex-1 items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 shadow-inner">
                <input
                  type="text"
                  placeholder="Type your message..."
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      sendMessage();
                    }
                  }}
                  className="flex-1 border-0 bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
                />
              </div>

              <button
                onClick={sendMessage}
                className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
              >
                Send
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

