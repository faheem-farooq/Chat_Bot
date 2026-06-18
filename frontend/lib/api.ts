const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Conversation = { id: number; title: string; summary?: string | null };
export type Message = { id: number; role: "user" | "assistant"; content: string };

export function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  conversations: () => request<Conversation[]>("/conversations"),
  messages: (id: number) => request<Message[]>(`/conversations/${id}/messages`),
  memories: () => request<string[]>("/memories"),
  addMemory: (content: string) =>
    request<{ ok: boolean }>("/memories", { method: "POST", body: JSON.stringify({ content }) }),
  chat: (message: string, conversationId: number | null, useWeb: boolean, useRag: boolean) =>
    request<{ conversation_id: number; answer: string; title: string; summary?: string | null }>("/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId, use_web: useWeb, use_rag: useRag })
    }),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ chunks_added: number }>("/documents", { method: "POST", body: form });
  },
  image: (file: File, prompt: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("prompt", prompt);
    return request<{ answer: string }>("/image", { method: "POST", body: form });
  }
};
