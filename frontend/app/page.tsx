"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Bot, Brain, FolderClosed, Globe, ImagePlus, LogOut, MessageSquare, Mic, Plus, Send, Upload } from "lucide-react";
import { api, clearToken, Conversation, getToken, Message, setToken } from "@/lib/api";

declare global {
  interface Window {
    webkitSpeechRecognition?: new () => SpeechRecognition;
    SpeechRecognition?: new () => SpeechRecognition;
  }
}

type SpeechRecognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult: ((event: { results: { [key: number]: { [key: number]: { transcript: string } } } }) => void) | null;
};

export default function Home() {
  const [tokenReady, setTokenReady] = useState(false);
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("password123");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [memory, setMemory] = useState("");
  const [memories, setMemories] = useState<string[]>([]);
  const [useWeb, setUseWeb] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [notice, setNotice] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const imageRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    Promise.resolve().then(() => setTokenReady(Boolean(getToken())));
  }, []);

  useEffect(() => {
    if (tokenReady) refresh();
  }, [tokenReady]);

  async function refresh() {
    const [chatList, memoryList] = await Promise.all([api.conversations(), api.memories()]);
    setConversations(chatList);
    setMemories(memoryList);
  }

  async function auth(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const result = mode === "login" ? await api.login(email, password) : await api.register(email, password);
      setToken(result.access_token);
      setTokenReady(true);
      setNotice("");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Auth failed");
    } finally {
      setBusy(false);
    }
  }

  async function openConversation(id: number) {
    setConversationId(id);
    setMessages(await api.messages(id));
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!input.trim()) return;
    const text = input.trim();
    setInput("");
    setBusy(true);
    setMessages((items) => [...items, { id: Date.now(), role: "user", content: text }]);
    try {
      const result = await api.chat(text, conversationId, useWeb, useRag);
      setConversationId(result.conversation_id);
      setMessages((items) => [...items, { id: Date.now() + 1, role: "assistant", content: result.answer }]);
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Chat failed");
    } finally {
      setBusy(false);
    }
  }

  async function uploadDocument(file?: File) {
    if (!file) return;
    setBusy(true);
    try {
      const result = await api.uploadDocument(file);
      setNotice(`Indexed ${result.chunks_added} document chunks.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function analyzeImage(file?: File) {
    if (!file) return;
    setBusy(true);
    try {
      const result = await api.image(file, input || "Describe this image.");
      setMessages((items) => [...items, { id: Date.now(), role: "assistant", content: result.answer }]);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Image analysis failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveMemory() {
    if (!memory.trim()) return;
    await api.addMemory(memory.trim());
    setMemory("");
    await refresh();
  }

  function startVoice() {
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }

    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setNotice("Voice input needs Chrome or Edge. Safari and Firefox often do not expose browser speech recognition.");
      return;
    }
    if (!window.isSecureContext) {
      setNotice("Voice input needs localhost or HTTPS so the browser can ask for microphone permission.");
      return;
    }

    const recognition = new Recognition();
    recognitionRef.current = recognition;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onstart = () => {
      setListening(true);
      setNotice("Listening...");
    };
    recognition.onend = () => {
      setListening(false);
      setNotice("");
    };
    recognition.onerror = (event) => {
      setListening(false);
      setNotice(`Voice input stopped: ${event.error}. Check microphone permission in the browser.`);
    };
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput((current) => `${current}${current ? " " : ""}${transcript}`.trim());
    };

    try {
      recognition.start();
    } catch {
      setListening(false);
      setNotice("Voice input could not start. Try allowing microphone permission and click the mic again.");
    }
  }

  if (!tokenReady) {
    return (
      <main className="auth-shell">
        <form className="auth-card" onSubmit={auth}>
          <div className="brand">
            <Bot size={30} />
            <div>
              <h1>Learning Chatbot</h1>
              <p>FastAPI, Next.js, Postgres, RAG, Groq.</p>
            </div>
          </div>
          <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" />
          <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" type="password" />
          <button disabled={busy}>{mode === "login" ? "Log in" : "Create account"}</button>
          <button className="link-button" type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? "Need an account?" : "Already have an account?"}
          </button>
          {notice && <p className="notice">{notice}</p>}
        </form>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="side-header">
          <div className="side-brand">
            <div className="mark"><Bot size={18} /></div>
            <span>Learning Chatbot</span>
          </div>
          <button
            className="icon-button"
            title="Log out"
            onClick={() => {
              clearToken();
              setTokenReady(false);
            }}
          >
            <LogOut size={18} />
          </button>
        </div>
        <button className="new-chat" onClick={() => { setConversationId(null); setMessages([]); }}>
          <Plus size={17} />
          New chat
        </button>

        <details className="history-folder" open>
          <summary>
            <span><FolderClosed size={15} /> Previous chats</span>
            <small>{conversations.length}</small>
          </summary>
          <div className="history">
            {conversations.map((conversation) => (
              <button key={conversation.id} className={conversation.id === conversationId ? "active" : ""} onClick={() => openConversation(conversation.id)} title={conversation.summary || conversation.title}>
                <MessageSquare size={15} />
                <span>
                  <strong>{conversation.title}</strong>
                  {conversation.summary && <small>{conversation.summary}</small>}
                </span>
              </button>
            ))}
          </div>
        </details>

        <div className="sidebar-tools">
          <section>
            <div className="tool-title">
              <Upload size={16} />
              <span>Documents</span>
            </div>
            <button className="tool-button" onClick={() => fileRef.current?.click()}>Upload file</button>
            <input ref={fileRef} hidden type="file" accept=".txt,.md,.csv" onChange={(event) => uploadDocument(event.target.files?.[0])} />
          </section>
          <section>
            <div className="tool-title">
              <Brain size={16} />
              <span>Memory</span>
            </div>
            <textarea value={memory} onChange={(event) => setMemory(event.target.value)} placeholder="Save a preference..." />
            <button className="tool-button" onClick={saveMemory}>Save memory</button>
            <div className="memory-list">
              {memories.slice(0, 3).map((item, index) => <p key={index}>{item}</p>)}
            </div>
          </section>
        </div>
      </aside>

      <section className="chat-panel">
        <header className="topbar">
          <div>
            <h1>{conversationId ? "Chat" : "New chat"}</h1>
          </div>
          <div className="toggles">
            <label className={useRag ? "enabled" : ""}><input type="checkbox" checked={useRag} onChange={(event) => setUseRag(event.target.checked)} /> <Brain size={16} /> RAG</label>
            <label className={useWeb ? "enabled" : ""}><input type="checkbox" checked={useWeb} onChange={(event) => setUseWeb(event.target.checked)} /> <Globe size={16} /> Web</label>
          </div>
        </header>

        <div className="messages">
          {messages.length === 0 && (
            <div className="empty">
              <div className="empty-mark"><Bot size={28} /></div>
              <h2>What can I help with?</h2>
              <div className="prompt-chips">
                <button type="button" onClick={() => setInput("Explain how RAG works in this project.")}>Explain RAG</button>
                <button type="button" onClick={() => setInput("Summarize my uploaded notes.")}>Summarize notes</button>
                <button type="button" onClick={() => setInput("Remember that I prefer simple Python examples.")}>Save a preference</button>
              </div>
            </div>
          )}
          {messages.map((message) => (
            <article key={message.id} className={`message-row ${message.role}`}>
              <div className="avatar">{message.role === "assistant" ? <Bot size={16} /> : "You"}</div>
              <div className="bubble">
                <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
                <p>{message.content}</p>
              </div>
            </article>
          ))}
        </div>

        {notice && <p className="notice chat-notice">{notice}</p>}

        <div className="composer-wrap">
          <form className="composer" onSubmit={sendMessage}>
            <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Message Learning Chatbot" />
            <div className="composer-actions">
              <button type="button" className={listening ? "listening" : ""} title={listening ? "Stop listening" : "Voice input"} onClick={startVoice}><Mic size={18} /></button>
              <button type="button" title="Analyze image" onClick={() => imageRef.current?.click()}><ImagePlus size={18} /></button>
              <button disabled={busy || !input.trim()} title="Send"><Send size={18} /></button>
            </div>
            <input ref={imageRef} hidden type="file" accept="image/*" onChange={(event) => analyzeImage(event.target.files?.[0])} />
          </form>
          <p className="fine-print">Learning project UI. Check important answers before using them.</p>
        </div>
      </section>
    </main>
  );
}
