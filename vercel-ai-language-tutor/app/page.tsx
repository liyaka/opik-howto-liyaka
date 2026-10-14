"use client";

import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";

export default function TutorPage() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ body: { lessonId: "cafe-ordering" } }),
  });
  const busy = status === "submitted" || status === "streaming";

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 style={{ fontSize: "1.25rem" }}>Profe Marisol: cafe Spanish</h1>
      {messages.map((m) => (
        <p key={m.id} style={{ whiteSpace: "pre-wrap", color: m.role === "user" ? "#1a56c4" : "#111" }}>
          <b>{m.role === "user" ? "You" : "Profe"}:</b>{" "}
          {m.parts.map((p, i) => (p.type === "text" ? <span key={i}>{p.text}</span> : null))}
        </p>
      ))}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!input.trim() || busy) return;
          void sendMessage({ text: input });
          setInput("");
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Try: Yo quiero un cafe por favor, y la cuenta"
          style={{ width: "100%", padding: "0.6rem", boxSizing: "border-box" }}
        />
      </form>
    </main>
  );
}
