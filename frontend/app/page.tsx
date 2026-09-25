"use client";

import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");

  async function testBackend() {
    const response = await fetch("http://127.0.0.1:8000/api/test");
    const data = await response.json();

    setMessage(data.message);
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6">
      <h1 className="text-3xl font-bold">
        AI Knowledge & Research Assistant
      </h1>

      <button
        onClick={testBackend}
        className="px-5 py-3 rounded-lg bg-black text-white"
      >
        Test Backend
      </button>

      {message && (
        <p className="text-lg">
          Backend says: {message}
        </p>
      )}
    </main>
  );
}