"use client";

import { useEffect, useRef, useState } from "react";
import { streamChat } from "@/lib/api";
import type { ChatMessage, ChatSource } from "@/lib/types";

const STARTERS = [
  "Why did Video A get more engagement than Video B?",
  "What's the engagement rate of each?",
  "Compare the hooks in the first 5 seconds.",
  "Who's the creator of Video B and what's their follower count?",
  "Suggest improvements for B based on what worked in A.",
];

interface Props {
  sessionId: string | null;
  disabled: boolean;
}

export function ChatPanel({ sessionId, disabled }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
    setInput("");
  }, [sessionId]);

  const scrollDown = () => {
    requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }));
  };

  const send = async (text: string) => {
    if (!sessionId || !text.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    scrollDown();

    let assistant = "";
    let sources: ChatSource[] = [];

    try {
      for await (const event of streamChat(sessionId, text.trim())) {
        if (event.type === "token") {
          assistant += event.content;
          setMessages((m) => {
            const copy = [...m];
            const last = copy[copy.length - 1];
            if (last?.role === "assistant") {
              copy[copy.length - 1] = { ...last, content: assistant, sources };
            } else {
              copy.push({ role: "assistant", content: assistant, sources });
            }
            return copy;
          });
          scrollDown();
        } else if (event.type === "sources") {
          sources = event.sources;
        }
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Chat error";
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${msg}` }]);
    } finally {
      setLoading(false);
      scrollDown();
    }
  };

  return (
    <section className="chat">
      <h2 className="chat-title">Creator chat</h2>
      <p className="chat-sub">Answers stream with transcript citations · memory on</p>

      <div className="messages">
        {messages.length === 0 && (
          <p className="empty">Ask anything about Video A vs B. Try a starter below.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <p>{m.content}</p>
            {m.sources && m.sources.length > 0 && (
              <ul className="sources">
                {m.sources.map((s, j) => (
                  <li key={j}>
                    <strong>Video {s.video_id}</strong> chunk {s.chunk_index}
                    {s.is_hook ? " · hook" : ""}
                    {s.platform ? ` (${s.platform})` : ""}: {s.snippet}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="starters">
        {STARTERS.map((q) => (
          <button
            key={q}
            type="button"
            className="starter"
            disabled={disabled || loading}
            onClick={() => send(q)}
          >
            {q}
          </button>
        ))}
      </div>

      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={disabled ? "Ingest videos first…" : "Ask about engagement, hooks, creators…"}
          disabled={disabled || loading}
        />
        <button type="submit" disabled={disabled || loading || !input.trim()}>
          {loading ? "…" : "Send"}
        </button>
      </form>
    </section>
  );
}
