export type ChatRequest = {
  userId: string;
  threadId: string;
  message: string;
};

export type ChatResponse = {
  answer: string;
  user_id: string;
  thread_id: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: payload.userId,
      thread_id: payload.threadId,
      message: payload.message
    })
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "请求失败");
  }

  return (await response.json()) as ChatResponse;
}
