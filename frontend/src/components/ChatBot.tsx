import { useState, useRef, useEffect, type FC } from "react";
import { chatWithRuko, type ChatMsg, type CheckResult } from "../lib/api";

interface Props {
  scanResult?: CheckResult | null;
}

const STARTERS = [
  "What are the red flags in my scan?",
  "How do I verify SEBI registration?",
  "I already transferred money — what now?",
  "What is the Cyber Crime helpline?",
];

const TypingDots: FC = () => (
  <span className="inline-flex items-end gap-[3px] h-4">
    {[0, 1, 2].map((i) => (
      <span
        key={i}
        className="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce"
        style={{ animationDelay: `${i * 150}ms`, animationDuration: "0.8s" }}
      />
    ))}
  </span>
);

const RukoAvatar: FC = () => (
  <div className="relative shrink-0 flex items-center justify-center w-8 h-8 rounded-full border border-cyan-400/40 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 shadow-lg shadow-cyan-500/20">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-cyan-400">
      <rect x="2" y="2" width="20" height="20" rx="5" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M7 6h10M7 10h8M9 6v8c0 0 6 0 6-4s-6-4-6-4l7 10"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
    <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-background" />
  </div>
);

export const ChatBot: FC<Props> = ({ scanResult }) => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pulse, setPulse] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Stop pulsing after 6s
  useEffect(() => {
    const t = setTimeout(() => setPulse(false), 6000);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 300);
      if (messages.length === 0) {
        // Show welcome message
        setMessages([
          {
            role: "assistant",
            content: scanResult
              ? `I've reviewed your scan — **${Math.round(scanResult.score * 100)}% fraud risk** detected. Ask me anything about these results or how to stay safe.`
              : "Namaste 🙏 I'm **Ruko AI**, your investment fraud prevention assistant. Paste a suspicious message or ask me anything about scam detection, SEBI verification, or fraud recovery.",
          },
        ]);
      }
    }
  }, [open]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setInput("");

    const updated: ChatMsg[] = [...messages, { role: "user", content: trimmed }];
    setMessages(updated);
    setLoading(true);

    try {
      const resp = await chatWithRuko(updated, scanResult ?? undefined);
      setMessages([...updated, { role: "assistant", content: resp.reply }]);
    } catch {
      setMessages([
        ...updated,
        {
          role: "assistant",
          content:
            "Connection issue. For urgent fraud help, call **1930** (Cyber Crime Helpline) or visit **cybercrime.gov.in**.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>");
  };

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-6 right-6 z-[100]">
        {/* Tooltip */}
        {!open && pulse && (
          <div className="absolute -top-12 right-0 whitespace-nowrap rounded-xl border border-cyan-500/40 bg-background/95 backdrop-blur px-3 py-1.5 label-mono text-xs text-cyan-400 shadow-lg shadow-cyan-500/20 animate-fade-in">
            Ask Ruko AI ✦
            <span className="absolute -bottom-1.5 right-4 w-3 h-3 bg-background/95 border-r border-b border-cyan-500/40 rotate-45" />
          </div>
        )}

        {/* Pulse rings */}
        {!open && pulse && (
          <>
            <span className="absolute inset-0 rounded-full bg-cyan-400/20 animate-ping" />
            <span className="absolute inset-[-4px] rounded-full border border-cyan-400/30 animate-pulse" />
          </>
        )}

        <button
          onClick={() => setOpen(!open)}
          aria-label={open ? "Close chat" : "Open Ruko AI chat"}
          className={`relative flex items-center justify-center w-14 h-14 rounded-full shadow-xl transition-all duration-300 active:scale-95
            ${
              open
                ? "bg-foreground text-background rotate-90 shadow-black/30"
                : "bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-cyan-500/40 hover:shadow-cyan-500/60 hover:scale-110"
            }`}
        >
          {open ? (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          ) : (
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
          )}
        </button>
      </div>

      {/* Chat Panel */}
      <div
        className={`fixed bottom-24 right-6 z-[99] w-[calc(100vw-3rem)] max-w-sm transition-all duration-300 origin-bottom-right
          ${open ? "opacity-100 scale-100 translate-y-0 pointer-events-auto" : "opacity-0 scale-95 translate-y-4 pointer-events-none"}`}
      >
        <div
          className="flex flex-col rounded-2xl border border-border/80 bg-card/95 backdrop-blur-2xl shadow-2xl shadow-black/40 overflow-hidden"
          style={{ height: "520px" }}
        >
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-gradient-to-r from-cyan-500/10 to-blue-600/10 shrink-0">
            <RukoAvatar />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-foreground font-mono">Ruko AI</span>
                <span className="label-mono text-[9px] px-1.5 py-0.5 rounded border border-cyan-500/40 bg-cyan-500/10 text-cyan-400">
                  LIVE
                </span>
              </div>
              <p className="label-mono text-[10px] text-muted-foreground truncate">
                Investment Fraud Expert · Groq Llama 3.3-70b
              </p>
            </div>
            {scanResult && (
              <div
                className={`label-mono text-[10px] px-2 py-1 rounded-lg border font-bold
                ${
                  scanResult.score >= 0.41
                    ? "border-red-500/40 bg-red-500/10 text-red-400"
                    : "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                }`}
              >
                {Math.round(scanResult.score * 100)}% risk
              </div>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 scrollbar-thin">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"} animate-slide-in`}
              >
                {msg.role === "assistant" && <RukoAvatar />}
                <div
                  className={`max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm
                    ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                        : "bg-secondary/80 text-foreground rounded-tl-sm border border-border/60"
                    }`}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                />
              </div>
            ))}

            {loading && (
              <div className="flex gap-2.5 animate-slide-in">
                <RukoAvatar />
                <div className="bg-secondary/80 border border-border/60 rounded-2xl rounded-tl-sm px-4 py-3">
                  <TypingDots />
                </div>
              </div>
            )}

            {/* Quick starters — shown only if no user messages yet */}
            {messages.length <= 1 && !loading && (
              <div className="pt-1 space-y-1.5">
                {STARTERS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="w-full text-left text-xs px-3 py-2 rounded-xl border border-border/70 bg-background/50 text-muted-foreground hover:border-cyan-500/50 hover:text-cyan-400 hover:bg-cyan-500/5 transition-all duration-200 label-mono"
                  >
                    ✦ {s}
                  </button>
                ))}
              </div>
            )}

            <div ref={endRef} />
          </div>

          {/* Input */}
          <div className="px-3 pb-3 pt-2 border-t border-border/60 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              className="flex items-center gap-2 rounded-xl border border-border bg-background/80 px-3 py-2 focus-within:border-cyan-400/60 transition-colors"
            >
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about this scan or scam patterns…"
                disabled={loading}
                className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/60 outline-none min-w-0"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="shrink-0 flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-primary-foreground disabled:opacity-40 hover:opacity-90 active:scale-95 transition-all"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
              </button>
            </form>
            <p className="text-center label-mono text-[9px] text-muted-foreground/50 mt-1.5">
              Powered by Groq · Not financial advice · Emergency: 1930
            </p>
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatBot;
