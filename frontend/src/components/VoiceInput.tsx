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

  const startRecording = async () => {
    setError(null);
    setState("recording");
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRef.current = mr;

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setState("processing");
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await sendToBackend(blob);
      };

      mr.start();
    } catch (err) {
      setError("Microphone access denied. Please allow microphone permissions.");
      setState("idle");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
  };

  const sendToBackend = async (blob: Blob) => {
    try {
      const file = new File([blob], "voice.webm", { type: "audio/webm" });
      const fd = new FormData();
      fd.append("file", file);
      if (lang) fd.append("language", lang);

      const res = await fetch("/v1/check/media", { method: "POST", body: fd });
      const data = await res.json();

      if (res.ok && data.text) {
        onTranscript(data.text);
        setState("idle");
        return;
      }
      // If backend returns a result without text, still use speech_text if available
      if (res.ok && data.speech_text) {
        onTranscript(data.speech_text);
        setState("idle");
        return;
      }
      throw new Error("No transcript in response");
    } catch {
      // Fallback: browser Web Speech API
      fallbackBrowserSTT();
    }
  };

  const fallbackBrowserSTT = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Voice transcription failed. Please type your message.");
      setState("idle");
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = lang === "hi" ? "hi-IN" : lang === "gu" ? "gu-IN" : "en-IN";
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      onTranscript(transcript);
      setState("idle");
    };
    rec.onerror = () => {
      setError("Could not transcribe. Please type your message.");
      setState("idle");
    };
    rec.start();
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
          ${
            isRecording
              ? "border-red-500/60 bg-red-500/10 text-red-400 animate-pulse shadow-lg shadow-red-500/20"
              : isProcessing
                ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-400"
                : "border-border bg-card/60 text-muted-foreground hover:border-cyan-400/60 hover:text-cyan-400 hover:bg-cyan-500/5"
          }`}
      >
        {isProcessing ? (
          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="2"
              strokeOpacity="0.3"
            />
            <path
              d="M12 2a10 10 0 0110 10"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        ) : isRecording ? (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="4" y="4" width="16" height="16" rx="2" />
          </svg>
        ) : (
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
            <path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" />
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
        <p className="label-mono text-[10px] text-destructive text-center max-w-[160px] leading-relaxed">
          {error}
        </p>
      )}
    </div>
  );
};

export default VoiceInput;
