import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect, type FormEvent } from "react";
import { AlertCircle, Bot, Loader2, RotateCcw, Send, Sparkles, User } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/_app/chat")({
  component: ChatPage,
});

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  error?: boolean;
  timestamp: Date;
}

const EXAMPLE_PROMPTS = [
  "What medications do I have scheduled today?",
  "Are there any food interactions with my medicines?",
  "What should I do if I miss a scheduled dose?",
];

function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string>(() =>
    `sess-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
  );
  const [input, setInput] = useState("");
  const [isPending, setIsPending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isPending]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isPending) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsPending(true);

    try {
      // Cap history to the last 6 messages (hard limit to bound token cost and maintain flat latency)
      const historyPayload = messages
        .filter((m) => !m.error && m.content)
        .slice(-6)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const res = await api.post<{ response: string }>("/ai/chat", {
        message: trimmed,
        history: historyPayload,
        session_id: sessionId,
      });
      const assistantMessage: ChatMessage = {
        id: `ai-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        role: "assistant",
        content: res.response ?? "No response generated.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorText =
        err instanceof ApiError
          ? err.message
          : "Unable to communicate with the health assistant. Please check your connection and try again.";
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        role: "assistant",
        content: errorText,
        error: true,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsPending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const clearChat = () => {
    if (sessionId) {
      api.post("/ai/chat/clear", { session_id: sessionId }).catch(() => {});
    }
    setMessages([]);
    setInput("");
    setSessionId(`sess-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`);
  };

  const userInitials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((p) => p[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "ME";

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] max-w-5xl mx-auto">
      <div className="flex items-center justify-between shrink-0 mb-3">
        <PageHeader
          title="Health Assistant"
          description="Ask MediSync AI about your medications, food interactions, and daily schedule."
        />
        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
            disabled={isPending}
            className="rounded-full text-xs text-muted-foreground hover:text-foreground gap-1.5"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Clear chat
          </Button>
        )}
      </div>

      <Card className="flex-1 flex flex-col min-h-0 rounded-2xl border-border bg-card overflow-hidden shadow-xs">
        {/* Messages scroll area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4 py-8 my-auto">
              <div className="h-14 w-14 rounded-2xl bg-accent text-accent-foreground flex items-center justify-center mb-4 shadow-xs">
                <Sparkles className="h-7 w-7 text-primary" />
              </div>
              <h2 className="text-lg font-semibold tracking-tight">How can I help you today?</h2>
              <p className="text-sm text-muted-foreground max-w-md mt-1 mb-6">
                I can review your current medications, check interactions, or answer questions about your personalized schedule.
              </p>

              <div className="flex flex-wrap gap-2 justify-center max-w-xl">
                {EXAMPLE_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => sendMessage(prompt)}
                    disabled={isPending}
                    className="text-xs bg-muted/60 hover:bg-accent hover:text-accent-foreground border border-border/70 rounded-full px-3.5 py-2 transition-colors cursor-pointer text-left"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((m) => {
                const isUser = m.role === "user";
                return (
                  <div
                    key={m.id}
                    className={`flex gap-3 items-start ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    {!isUser && (
                      <div className="h-8 w-8 rounded-full bg-accent text-accent-foreground flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                    )}

                    <div
                      className={`rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-[85%] sm:max-w-[75%] ${
                        isUser
                          ? "bg-primary text-primary-foreground rounded-tr-xs shadow-xs"
                          : m.error
                            ? "bg-destructive/10 border border-destructive/25 text-destructive rounded-tl-xs"
                            : "bg-muted/50 border border-border/60 text-foreground rounded-tl-xs whitespace-pre-wrap"
                      }`}
                    >
                      {m.error && (
                        <div className="flex items-center gap-1.5 font-medium mb-1 text-xs">
                          <AlertCircle className="h-3.5 w-3.5" />
                          <span>Error</span>
                        </div>
                      )}
                      <div>{m.content}</div>
                    </div>

                    {isUser && (
                      <Avatar className="h-8 w-8 shrink-0 mt-0.5 border border-border">
                        <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                          {userInitials || <User className="h-4 w-4" />}
                        </AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                );
              })}

              {isPending && (
                <div className="flex gap-3 items-start justify-start">
                  <div className="h-8 w-8 rounded-full bg-accent text-accent-foreground flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                  </div>
                  <div className="bg-muted/50 border border-border/60 rounded-2xl rounded-tl-xs px-4 py-3 text-sm flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                    <span>MediSync AI is thinking…</span>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input pinned at bottom */}
        <div className="p-3 md:p-4 border-t border-border bg-card">
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about medications, interactions, or schedule..."
              disabled={isPending}
              className="flex-1 rounded-full px-4 h-11 bg-muted/30 focus-visible:bg-background"
            />
            <Button
              type="submit"
              disabled={!input.trim() || isPending}
              className="rounded-full h-11 px-5 gap-2 shrink-0 shadow-xs"
            >
              {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              <span className="hidden sm:inline">Send</span>
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
