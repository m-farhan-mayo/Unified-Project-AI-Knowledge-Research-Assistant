"use client";

import { useRef, useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  emailStatus?: EmailStatus;
};

type EmailStatus = {
  success: boolean;
  message: string;
  recipient?: string;
  subject?: string;
};

type Source = {
  type?: "web" | "document";

  title?: string;
  url?: string;

  filename?: string;

  document_id?: number;

  page_number?: number;

  chunk_index?: number;

  chunk_id?: number;

  distance?: number;
};

async function readResponse(response: Response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string"
      ? data.detail
      : `Request failed (${response.status}). Check that the backend is running.`;
    throw new Error(detail);
  }
  if (!data) throw new Error("The server returned an invalid response.");
  return data;
}

export default function Home() {
  const sessionId = useRef("");
  const fileInput = useRef<HTMLInputElement>(null);
  const requestPending = useRef(false);

  function getSessionId() {
    if (!sessionId.current) {
      sessionId.current = `session-${Array.from(window.crypto.getRandomValues(new Uint32Array(4)), value => value.toString(16)).join("-")}`;
    }
    return sessionId.current;
  }
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeDocumentId, setActiveDocumentId] =
  useState<number | null>(null);

  const [activeDocumentName, setActiveDocumentName] =
  useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Start a conversation and I’ll help you organize your ideas, research, and notes.",
    },
  ]);

  async function sendMessage() {
    const text = message.trim();
    if ((!text && !selectedFile) || requestPending.current) return;
    requestPending.current = true;

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
      let responseSources: Source[] = [];
      let responseEmailStatus: EmailStatus | undefined;

      let documentId = activeDocumentId;
      if (selectedFile) {
        const formData = new FormData();

        formData.append(
          "file",
          selectedFile
        );

        const uploadResult = await fetch(
          "/api/upload-pdf",
          {
            method: "POST",
            body: formData,
          }
        );

        const uploadedData =
          await readResponse(uploadResult);

        if (!uploadResult.ok) {
          throw new Error(
            uploadedData.detail ||
            `PDF upload failed (${uploadResult.status}).`
          );
        }

        documentId = uploadedData.document_id;
        setActiveDocumentId(documentId);

        setActiveDocumentName(
          uploadedData.filename
        );

        responseText =
          `Successfully indexed ${uploadedData.filename}.\n\n` +
          `Pages: ${uploadedData.total_pages}\n` +
          `Chunks: ${uploadedData.total_chunks}\n\n` +
          `You can now ask questions about this document.`;
      }

      if (text) {
        const result = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
          session_id: getSessionId(),
          message: text,
          document_id: documentId,
        }),
        });

        const data = await readResponse(result);
        if (!result.ok) {
          throw new Error(data.detail || `Chat request failed (${result.status}).`);
        }
        if (typeof data.response === "string") {
          responseText = data.response;
        } else {
          responseText = data.response?.answer || "No response received.";
          responseSources = Array.isArray(data.response?.sources)
            ? data.response.sources
            : [];
          responseEmailStatus = data.response?.email_status;
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: responseText,
          sources: responseSources,
          emailStatus: responseEmailStatus,
        },
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
      if (fileInput.current) fileInput.current.value = "";
      requestPending.current = false;
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
              sessionId.current = "";
              if (fileInput.current) fileInput.current.value = "";
              setMessages([{
                role: "assistant",
                content: "Start a conversation and I’ll help you organize your ideas, research, and notes.",
              }]);
              setMessage("");
              setSelectedFile(null);
              setActiveDocumentId(null);
              setActiveDocumentName(null);
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
              {loading ? "Working" : "Ready"}
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
                  <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 border-t border-current/15 pt-2">
                      <p className="mb-1 text-xs font-semibold">Sources</p>
                      <ul className="space-y-1">
                        {msg.sources.map((source, sourceIndex) => (
                          <li key={`${source.url ?? source.title ?? "source"}-${sourceIndex}`}>
                            {source.url && /^https?:\/\//i.test(source.url) ? (
                              <a
                                href={source.url}
                                target="_blank"
                                rel="noreferrer"
                                className="underline underline-offset-2"
                              >
                                {source.title || source.url}
                              </a>
                            ) : source.filename ? (
                              <span>
                                {source.filename}

                                {source.page_number !== undefined &&
                                  ` — Page ${source.page_number}`}

                                {source.chunk_index !== undefined &&
                                  ` — Chunk ${source.chunk_index + 1}`}
                              </span>
                            ) : (
                              source.title ||
                              `Source ${sourceIndex + 1}`
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {msg.emailStatus && (
                    <p className={`mt-2 border-t border-current/15 pt-2 text-xs ${msg.emailStatus.success ? "text-emerald-700" : "text-red-700"}`}>
                      {msg.emailStatus.message}
                    </p>
                  )}
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
            {activeDocumentName && (
              <div className="mb-3 flex items-center gap-3 text-sm">
                <span>Document: {activeDocumentName}</span>
                <button disabled={loading} className="underline" onClick={() => {
                  setActiveDocumentId(null);
                  setActiveDocumentName(null);
                  sessionId.current = "";
                }}>Stop using document</button>
              </div>
            )}
            <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center">
              <label className="flex w-fit cursor-pointer items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 shadow-sm transition hover:bg-slate-100">
                <span>Attach PDF</span>
                <input
                  ref={fileInput}
                  disabled={loading}
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
                    if (event.key === "Enter" && !event.nativeEvent.isComposing) {
                      sendMessage();
                    }
                  }}
                  className="flex-1 border-0 bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
                />
              </div>

              <button
                disabled={loading || (!message.trim() && !selectedFile)}
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

