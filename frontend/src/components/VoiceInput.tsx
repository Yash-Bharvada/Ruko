/**
 * VoiceInput — records microphone audio and transcribes via Sarvam STT backend.
 * Falls back to browser Web Speech API if backend STT is unavailable.
 */
import { useState, useRef, type FC } from "react";

interface Props {
  onTranscript: (text: string) => void;
  lang?: string;
}

export const VoiceInput: FC<Props> = ({ onTranscript, lang = "en" }) => {
  const [state, setState] = useState<"idle" | "recording" | "processing">("idle");
  const [error, setError] = useState<string | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const liveTranscriptRef = useRef<string>("");
  const speechRecRef = useRef<any>(null);

  const startRecording = async () => {
    setError(null);
    setState("recording");
    chunksRef.current = [];
    liveTranscriptRef.current = "";

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      let mimeType = "";
      if (typeof MediaRecorder !== "undefined" && typeof MediaRecorder.isTypeSupported === "function") {
        if (MediaRecorder.isTypeSupported("audio/webm")) {
          mimeType = "audio/webm";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
          mimeType = "audio/mp4";
        }
      }

      const mr = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRef.current = mr;

      // Start concurrent real-time SpeechRecognition if available in browser
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const rec = new SpeechRecognition();
          rec.lang = lang === "hi" ? "hi-IN" : lang === "gu" ? "gu-IN" : "en-IN";
          rec.continuous = true;
          rec.interimResults = true;
          rec.onresult = (e: any) => {
            let combined = "";
            for (let i = 0; i < e.results.length; i++) {
              combined += e.results[i][0].transcript;
            }
            if (combined.trim()) {
              liveTranscriptRef.current = combined.trim();
            }
          };
          rec.onerror = () => {};
          rec.start();
          speechRecRef.current = rec;
        } catch {
          // Ignore SpeechRecognition startup error, backend will transcribe
        }
      }

      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (speechRecRef.current) {
          try {
            speechRecRef.current.stop();
          } catch {}
          speechRecRef.current = null;
        }
        setState("processing");

        // If real-time browser recognition already captured speech, use it immediately
        if (liveTranscriptRef.current && liveTranscriptRef.current.trim().length >= 3) {
          onTranscript(liveTranscriptRef.current.trim());
          setState("idle");
          return;
        }

        const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
        await sendToBackend(blob, mimeType);
      };

      mr.start();
    } catch {
      setError("Microphone access denied. Please allow microphone permissions.");
      setState("idle");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
  };

  const sendToBackend = async (blob: Blob, mimeType: string) => {
    try {
      const ext = mimeType.includes("mp4") ? "m4a" : "webm";
      const file = new File([blob], `voice.${ext}`, { type: blob.type || mimeType || "audio/webm" });
      const fd = new FormData();
      fd.append("file", file);
      if (lang) fd.append("language", lang);

      const res = await fetch("/v1/check/media", { method: "POST", body: fd });
      const data = await res.json();

      if (res.ok) {
        const text = data.text || data.speech_text;
        if (text && text.trim().length >= 3) {
          onTranscript(text.trim());
          setState("idle");
          return;
        }
      }

      const err = data?.error?.message || "Could not transcribe audio. Please type your message.";
      setError(err);
      setState("idle");
    } catch {
      setError("Voice transcription failed. Please type your message.");
      setState("idle");
    }
  };

  const isRecording = state === "recording";
  const isProcessing = state === "processing";

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        title={isRecording ? "Stop recording" : "Record voice message"}
        className={`relative flex items-center justify-center w-10 h-10 rounded-full border transition-all duration-200 active:scale-95
          ${isRecording
            ? "border-red-500/60 bg-red-500/10 text-red-400 animate-pulse shadow-lg shadow-red-500/20"
            : isProcessing
            ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-400"
            : "border-border bg-card/60 text-muted-foreground hover:border-cyan-400/60 hover:text-cyan-400 hover:bg-cyan-500/5"
          }`}
      >
        {isProcessing ? (
          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeOpacity="0.3"/>
            <path d="M12 2a10 10 0 0110 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : isRecording ? (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="4" y="4" width="16" height="16" rx="2" />
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
            <path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"/>
          </svg>
        )}

        {/* Ripple ring when recording */}
        {isRecording && (
          <span className="absolute inset-[-4px] rounded-full border border-red-500/40 animate-ping" />
        )}
      </button>

      {/* Status label */}
      <span className="label-mono text-[10px] text-muted-foreground">
        {isRecording ? "Recording… tap to stop" : isProcessing ? "Transcribing…" : "Voice input"}
      </span>

      {error && (
        <p className="label-mono text-[10px] text-destructive text-center max-w-[160px] leading-relaxed">{error}</p>
      )}
    </div>
  );
};

export default VoiceInput;
