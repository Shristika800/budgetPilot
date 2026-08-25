import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import api from "../../services/api";
import type { ChatMessage } from "../../types/transaction";

const SUGGESTIONS = [
  "How much did I spend this month?",
  "How much did I spend on food?",
  "Show my recent transactions",
  "Give me budget advice",
];

function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 0,
      role: "assistant",
      text: "Hi! I'm your BudgetPilot assistant. Ask me about your spending, add transactions, or get budget advice.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now(),
      role: "user",
      text: trimmed,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post<{ message: string }>("/chat/", {
        message: trimmed,
      });

      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: res.data.message,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          text: "Sorry, something went wrong. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendMessage(input);
  }

  return (
    <div className="chat-panel">
      {/* Message list */}
      <div className="chat-messages" role="log" aria-live="polite">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-bubble ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"}`}
          >
            {/* Preserve newlines in multi-line assistant responses */}
            {msg.text.split("\n").map((line, i) => (
              <span key={i}>
                {line}
                {i < msg.text.split("\n").length - 1 && <br />}
              </span>
            ))}
          </div>
        ))}

        {loading && (
          <div className="chat-bubble chat-bubble-assistant chat-typing">
            <span />
            <span />
            <span />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips — shown only when no user messages yet */}
      {messages.length === 1 && (
        <div className="chat-suggestions">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              className="suggestion-chip"
              onClick={() => sendMessage(s)}
              type="button"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder="Ask about your spending..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={1000}
          disabled={loading}
          aria-label="Chat message"
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={!input.trim() || loading}
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;
