import { FormEvent, useMemo, useState } from "react";
import { sendChatMessage } from "../api/chat";

type Role = "user" | "assistant";

type Message = {
  id: string;
  role: Role;
  content: string;
};

function createMessage(role: Role, content: string): Message {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    content
  };
}

export function ChatWindow() {
  const [userId, setUserId] = useState("demo-user");
  const [threadId, setThreadId] = useState("web-default");
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    createMessage("assistant", "你好，我是 Lang Agent。请输入你的问题。")
  ]);
  const [error, setError] = useState("");

  const canSend = useMemo(() => !isSending && input.trim().length > 0, [input, isSending]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanInput = input.trim();
    if (!cleanInput) {
      return;
    }

    setError("");
    setInput("");
    setIsSending(true);
    setMessages((prev) => [...prev, createMessage("user", cleanInput)]);

    try {
      const response = await sendChatMessage({
        userId,
        threadId,
        message: cleanInput
      });
      setMessages((prev) => [...prev, createMessage("assistant", response.answer || "（无回复）")]);
    } catch (ex) {
      const text = ex instanceof Error ? ex.message : "未知错误";
      setError(`发送失败：${text}`);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="chat-container">
      <header className="chat-header">
        <h1>Lang Agent Web Chat</h1>
        <p></p>
      </header>

      <div className="chat-session-config">
        <label>
          User ID
          <input value={userId} onChange={(event) => setUserId(event.target.value)} />
        </label>
        <label>
          Thread ID
          <input value={threadId} onChange={(event) => setThreadId(event.target.value)} />
        </label>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <article key={msg.id} className={`chat-message ${msg.role}`}>
            <strong>{msg.role === "user" ? "你" : "助手"}</strong>
            <p>{msg.content}</p>
          </article>
        ))}
      </div>

      {error ? <div className="chat-error">{error}</div> : null}

      <form onSubmit={onSubmit} className="chat-input-form">
        <textarea
          placeholder="输入你的问题..."
          value={input}
          onChange={(event) => setInput(event.target.value)}
          rows={3}
        />
        <button type="submit" disabled={!canSend}>
          {isSending ? "发送中..." : "发送"}
        </button>
      </form>
    </section>
  );
}
