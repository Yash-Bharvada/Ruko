/**
 * Browser-based 1280x720 video composer and speech synthesizer.
 * Renders storyboards to HTML5 Canvas and combines with audio via Web Audio API and MediaRecorder.
 * Zero server-side video rendering, zero disk writes.
 */

import {
  Scene,
  DocExplanation,
  KeyPoint,
  Step,
  GlossaryItem,
  TimelineItem,
  speakExplainScene,
} from "./api";
import { drawFlowGraphToCanvas } from "@/components/explain/DiagramRenderer";

export interface CompositionProgress {
  stage: "audio" | "rendering" | "encoding" | "complete" | "error";
  sceneIndex: number;
  totalScenes: number;
  percent: number;
  message: string;
}

export interface RenderedAudioScene {
  scene: Scene;
  audioBuffer: AudioBuffer | null;
  durationMs: number;
  source: "sarvam" | "browser_speech" | "silent";
}

/**
 * Fetch TTS audio for all scenes sequentially
 */
export async function prepareSceneAudio(
  requestId: string,
  scenes: Scene[],
  language: string,
  audioCtx: AudioContext,
  onProgress?: (p: CompositionProgress) => void,
  abortSignal?: AbortSignal,
): Promise<RenderedAudioScene[]> {
  const results: RenderedAudioScene[] = [];
  const total = scenes.length;

  for (let i = 0; i < scenes.length; i++) {
    if (abortSignal?.aborted) {
      throw new Error("Video generation cancelled");
    }

    const scene = scenes[i];
    if (!scene) continue;
    onProgress?.({
      stage: "audio",
      sceneIndex: i,
      totalScenes: total,
      percent: Math.round(((i + 0.5) / total) * 35),
      message: `Preparing audio for scene ${i + 1} of ${total}...`,
    });

    // Default duration estimate (at ~2.2 words/sec)
    const wordCount = (scene.narration || scene.caption || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean).length;
    const estimatedMs = Math.max(Math.round((wordCount / 2.2) * 1000), 3500);

    try {
      const response = await speakExplainScene({
        request_id: requestId,
        scene_id: scene.scene_id,
        language: language,
        narration: scene.narration,
        issued_at: scene.issued_at,
        speak_token: scene.speak_token,
      });

      if (response.source === "sarvam" && response.audio_base64) {
        // Decode base64 to ArrayBuffer
        const binaryStr = atob(response.audio_base64);
        const len = binaryStr.length;
        const bytes = new Uint8Array(len);
        for (let j = 0; j < len; j++) {
          bytes[j] = binaryStr.charCodeAt(j);
        }
        const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer.slice(0));
        const durationMs = Math.max(Math.round(audioBuffer.duration * 1000), 3000);

        results.push({
          scene,
          audioBuffer,
          durationMs,
          source: "sarvam",
        });
      } else {
        // Browser speech fallback
        results.push({
          scene,
          audioBuffer: null,
          durationMs: estimatedMs,
          source: "browser_speech",
        });
      }
    } catch {
      // Offline / fallback path
      results.push({
        scene,
        audioBuffer: null,
        durationMs: estimatedMs,
        source: "browser_speech",
      });
    }
  }

  return results;
}

/**
 * Draw a single scene frame to 1280x720 canvas
 */
export function renderSceneFrame(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  scene: Scene,
  explanation: DocExplanation,
  sceneIndex: number,
  totalScenes: number,
  sceneProgress: number,
  totalProgress: number,
) {
  // Background gradient
  const bgGrad = ctx.createLinearGradient(0, 0, width, height);
  bgGrad.addColorStop(0, "#070c18");
  bgGrad.addColorStop(0.5, "#0b1329");
  bgGrad.addColorStop(1, "#050812");
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, width, height);

  // Subtle grid pattern
  ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
  ctx.lineWidth = 1;
  const gridSize = 40;
  for (let x = 0; x < width; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
  for (let y = 0; y < height; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  // Top header bar
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 20px system-ui, -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("RUKO DOCUMENT EXPLAINER", 50, 48);

  // Scene badge
  ctx.fillStyle = "rgba(59, 130, 246, 0.25)";
  ctx.strokeStyle = "rgba(59, 130, 246, 0.5)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(width - 180, 26, 130, 30, 15);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#60a5fa";
  ctx.font = "bold 12px system-ui, -apple-system, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(`SCENE ${sceneIndex + 1} / ${totalScenes}`, width - 115, 46);

  // Content Area
  const visual = scene.visual || { type: "title" };
  const visualType = (visual.type || "title").toLowerCase();
  const contentArea = { x: 60, y: 75, w: width - 120, h: height - 210 };

  if (visualType === "flowchart" && explanation.diagrams?.flowchart) {
    drawFlowGraphToCanvas(
      ctx,
      explanation.diagrams.flowchart,
      width / 2,
      contentArea.y + contentArea.h / 2,
      contentArea.w,
      contentArea.h,
      scene.caption || "Process Flowchart",
    );
  } else if (visualType === "money_flow" && explanation.diagrams?.money_flow) {
    drawFlowGraphToCanvas(
      ctx,
      explanation.diagrams.money_flow,
      width / 2,
      contentArea.y + contentArea.h / 2,
      contentArea.w,
      contentArea.h,
      scene.caption || "Money Flow",
    );
  } else if (visualType === "timeline" && explanation.diagrams?.timeline) {
    renderCanvasTimeline(ctx, explanation.diagrams.timeline, contentArea, sceneProgress);
  } else if (visualType === "bullets" && visual.ref === "steps" && explanation.steps) {
    renderCanvasSteps(ctx, explanation.steps, contentArea);
  } else if (visualType === "bullets" && explanation.key_points) {
    renderCanvasKeyPoints(ctx, explanation.key_points, contentArea);
  } else if (visualType === "glossary" && explanation.glossary) {
    renderCanvasGlossary(ctx, explanation.glossary, contentArea);
  } else {
    // Title / Overview / Summary scene
    renderCanvasSummary(
      ctx,
      scene.caption || "Overview",
      explanation.summary || scene.narration || "",
      contentArea,
    );
  }

  // Bottom Captions Bar
  const captionText = scene.narration || scene.caption || "";
  if (captionText) {
    const capHeight = 85;
    const capY = height - 125;
    ctx.fillStyle = "rgba(10, 15, 30, 0.9)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(50, capY, width - 100, capHeight, 14);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#f8fafc";
    ctx.font = "500 18px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "center";
    wrapText(ctx, captionText, width / 2, capY + 34, width - 160, 26, 2);
  }

  // Bottom progress bar
  const pbY = height - 10;
  ctx.fillStyle = "rgba(255, 255, 255, 0.1)";
  ctx.fillRect(0, pbY, width, 10);

  const progressGrad = ctx.createLinearGradient(0, pbY, width * totalProgress, pbY);
  progressGrad.addColorStop(0, "#3b82f6");
  progressGrad.addColorStop(1, "#8b5cf6");
  ctx.fillStyle = progressGrad;
  ctx.fillRect(0, pbY, Math.max(width * totalProgress, 6), 10);
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines: number = 3,
) {
  const words = String(text).split(" ");
  let line = "";
  let lineCount = 0;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const metrics = ctx.measureText(testLine);
    const testWidth = metrics.width;
    if (testWidth > maxWidth && n > 0) {
      if (lineCount === maxLines - 1 && n < words.length - 1) {
        ctx.fillText(line.trim() + "...", x, y);
        return;
      }
      ctx.fillText(line.trim(), x, y);
      line = words[n] + " ";
      y += lineHeight;
      lineCount++;
      if (lineCount >= maxLines) return;
    } else {
      line = testLine;
    }
  }
  ctx.fillText(line.trim(), x, y);
}

function renderCanvasSummary(
  ctx: CanvasRenderingContext2D,
  title: string,
  summary: string,
  area: { x: number; y: number; w: number; h: number },
) {
  ctx.fillStyle = "rgba(30, 41, 59, 0.65)";
  ctx.strokeStyle = "rgba(59, 130, 246, 0.35)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.roundRect(area.x, area.y, area.w, area.h, 16);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#38bdf8";
  ctx.font = "bold 24px system-ui, -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText(title, area.x + 35, area.y + 50);

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "400 20px system-ui, -apple-system, sans-serif";
  wrapText(ctx, summary, area.x + 35, area.y + 98, area.w - 70, 34, 5);
}

function renderCanvasKeyPoints(
  ctx: CanvasRenderingContext2D,
  keyPoints: KeyPoint[],
  area: { x: number; y: number; w: number; h: number },
) {
  ctx.fillStyle = "#a78bfa";
  ctx.font = "bold 22px system-ui, -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Key Obligations & Terms", area.x + 10, area.y + 30);

  const displayed = keyPoints.slice(0, 3);
  const cardH = Math.min((area.h - 50) / Math.max(displayed.length, 1), 75);

  displayed.forEach((kp, i) => {
    const cardY = area.y + 45 + i * (cardH + 12);
    ctx.fillStyle = "rgba(30, 41, 59, 0.75)";
    ctx.strokeStyle = "rgba(139, 92, 246, 0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(area.x, cardY, area.w, cardH, 12);
    ctx.fill();
    ctx.stroke();

    // Badge
    ctx.fillStyle = "#8b5cf6";
    ctx.beginPath();
    ctx.arc(area.x + 32, cardY + cardH / 2, 15, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 14px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${i + 1}`, area.x + 32, cardY + cardH / 2 + 5);

    // Text
    const pointText = kp.text || kp.point || "Key term";
    ctx.fillStyle = "#f1f5f9";
    ctx.font = "500 17px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "left";
    wrapText(ctx, pointText, area.x + 65, cardY + 28, area.w - 90, 24, 2);
  });
}

function renderCanvasSteps(
  ctx: CanvasRenderingContext2D,
  steps: Step[],
  area: { x: number; y: number; w: number; h: number },
) {
  ctx.fillStyle = "#34d399";
  ctx.font = "bold 22px system-ui, -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Next Steps & Action Plan", area.x + 10, area.y + 30);

  const displayed = steps.slice(0, 3);
  const cardH = Math.min((area.h - 50) / Math.max(displayed.length, 1), 75);

  displayed.forEach((step, i) => {
    const cardY = area.y + 45 + i * (cardH + 12);
    ctx.fillStyle = "rgba(30, 41, 59, 0.75)";
    ctx.strokeStyle = "rgba(16, 185, 129, 0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(area.x, cardY, area.w, cardH, 12);
    ctx.fill();
    ctx.stroke();

    // Step tag
    ctx.fillStyle = "#10b981";
    ctx.beginPath();
    ctx.roundRect(area.x + 18, cardY + 16, 68, 26, 6);
    ctx.fill();

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 12px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`STEP ${step.order || step.step_number || i + 1}`, area.x + 52, cardY + 33);

    // Step text
    const titleText = step.title || `Action ${i + 1}`;
    const descText = step.text || step.description || "";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 16px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(titleText, area.x + 100, cardY + 32);

    if (descText) {
      ctx.fillStyle = "#cbd5e1";
      ctx.font = "400 14px system-ui, -apple-system, sans-serif";
      wrapText(ctx, descText, area.x + 100, cardY + 54, area.w - 120, 20, 1);
    }
  });
}

function renderCanvasGlossary(
  ctx: CanvasRenderingContext2D,
  glossary: GlossaryItem[],
  area: { x: number; y: number; w: number; h: number },
) {
  ctx.fillStyle = "#fbbf24";
  ctx.font = "bold 22px system-ui, -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Key Financial Definitions", area.x + 10, area.y + 30);

  const displayed = glossary.slice(0, 2);
  const cardH = (area.h - 50) / Math.max(displayed.length, 1);

  displayed.forEach((item, i) => {
    const cardY = area.y + 45 + i * (cardH + 12);
    ctx.fillStyle = "rgba(30, 41, 59, 0.75)";
    ctx.strokeStyle = "rgba(245, 158, 11, 0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(area.x, cardY, area.w, cardH - 12, 12);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#fef08a";
    ctx.font = "bold 19px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(item.term, area.x + 25, cardY + 35);

    const meaningText = item.meaning || item.simple_explanation || "";
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "400 16px system-ui, -apple-system, sans-serif";
    wrapText(ctx, meaningText, area.x + 25, cardY + 68, area.w - 50, 24, 3);
  });
}

function renderCanvasTimeline(
  ctx: CanvasRenderingContext2D,
  timeline: TimelineItem[],
  area: { x: number; y: number; w: number; h: number },
  _sceneProgress: number,
) {
  ctx.fillStyle = "#38bdf8";
  ctx.font = "bold 22px system-ui, -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Timeline of Events & Obligations", area.x + 10, area.y + 30);

  const displayed = timeline.slice(0, 4);
  const count = displayed.length;
  const colW = (area.w - (count - 1) * 16) / Math.max(count, 1);

  displayed.forEach((item, i) => {
    const colX = area.x + i * (colW + 16);
    const colY = area.y + 50;
    const colH = area.h - 60;

    ctx.fillStyle = "rgba(30, 41, 59, 0.75)";
    ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(colX, colY, colW, colH, 12);
    ctx.fill();
    ctx.stroke();

    const dateText = item.date_text || item.time_reference || `Phase ${i + 1}`;
    const labelText = item.label || item.event || "Event";

    ctx.fillStyle = "#0284c7";
    ctx.beginPath();
    ctx.roundRect(colX + 12, colY + 16, colW - 24, 26, 6);
    ctx.fill();

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 12px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(dateText, colX + colW / 2, colY + 33);

    ctx.fillStyle = "#f8fafc";
    ctx.font = "bold 15px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "left";
    wrapText(ctx, labelText, colX + 12, colY + 68, colW - 24, 20, 4);
  });
}

/**
 * Compose full video file using MediaRecorder and AudioContext
 */
export async function composeStoryboardVideo(
  explanation: DocExplanation,
  scenesWithAudio: RenderedAudioScene[],
  onProgress?: (p: CompositionProgress) => void,
  abortSignal?: AbortSignal,
): Promise<{ videoBlob: Blob; objectUrl: string; hasAudio: boolean; totalDurationMs: number }> {
  const width = 1280;
  const height = 720;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Could not create canvas 2D context");

  const audioCtx = new (
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
  )();
  const dest = audioCtx.createMediaStreamDestination();

  // Keep a quiet silent oscillator connected to dest so the audio track clock runs smoothly
  const osc = audioCtx.createOscillator();
  const silenceGain = audioCtx.createGain();
  silenceGain.gain.value = 0.00001; // virtually silent
  osc.connect(silenceGain);
  silenceGain.connect(dest);
  osc.start();

  // Combine canvas video track + destination audio track
  const canvasStream = canvas.captureStream(30);
  const combinedStream = new MediaStream([
    ...canvasStream.getVideoTracks(),
    ...dest.stream.getAudioTracks(),
  ]);

  const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9,opus")
    ? "video/webm;codecs=vp9,opus"
    : MediaRecorder.isTypeSupported("video/webm;codecs=vp8,opus")
      ? "video/webm;codecs=vp8,opus"
      : "video/webm";

  const recorder = new MediaRecorder(combinedStream, { mimeType, videoBitsPerSecond: 2500000 });
  const chunks: Blob[] = [];

  recorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  };

  recorder.start(250); // Request chunks every 250ms

  const totalScenes = scenesWithAudio.length;
  const totalDurationMs = scenesWithAudio.reduce((sum, s) => sum + s.durationMs, 0);
  let accumulatedTimeMs = 0;
  let hasAnyAudio = false;

  for (let i = 0; i < scenesWithAudio.length; i++) {
    if (abortSignal?.aborted) {
      recorder.stop();
      osc.stop();
      audioCtx.close();
      throw new Error("Video generation cancelled");
    }

    const sceneData = scenesWithAudio[i];
    if (!sceneData) continue;
    const durationMs = sceneData.durationMs;

    // Play scene audio into destination
    if (sceneData.audioBuffer) {
      hasAnyAudio = true;
      const sourceNode = audioCtx.createBufferSource();
      sourceNode.buffer = sceneData.audioBuffer;
      sourceNode.connect(dest);
      sourceNode.start();
    }

    const fps = 30;
    const totalFrames = Math.max(Math.floor((durationMs / 1000) * fps), 20);
    const frameIntervalMs = 1000 / fps;

    for (let frame = 0; frame < totalFrames; frame++) {
      if (abortSignal?.aborted) {
        recorder.stop();
        osc.stop();
        audioCtx.close();
        throw new Error("Video generation cancelled");
      }

      const sceneProgress = frame / totalFrames;
      const currentGlobalMs = accumulatedTimeMs + sceneProgress * durationMs;
      const totalProgress = Math.min(currentGlobalMs / totalDurationMs, 1);

      renderSceneFrame(
        ctx,
        width,
        height,
        sceneData.scene,
        explanation,
        i,
        totalScenes,
        sceneProgress,
        totalProgress,
      );

      onProgress?.({
        stage: "rendering",
        sceneIndex: i,
        totalScenes,
        percent: Math.round(35 + totalProgress * 60),
        message: `Rendering scene ${i + 1} of ${totalScenes}...`,
      });

      await new Promise((r) => setTimeout(r, frameIntervalMs));
    }

    accumulatedTimeMs += durationMs;
  }

  onProgress?.({
    stage: "encoding",
    sceneIndex: totalScenes - 1,
    totalScenes,
    percent: 98,
    message: "Finalizing video file...",
  });

  const recordingFinished = new Promise<void>((resolve) => {
    recorder.onstop = () => resolve();
  });

  recorder.stop();
  await recordingFinished;
  osc.stop();
  await audioCtx.close();

  const videoBlob = new Blob(chunks, { type: mimeType });
  const objectUrl = URL.createObjectURL(videoBlob);

  onProgress?.({
    stage: "complete",
    sceneIndex: totalScenes - 1,
    totalScenes,
    percent: 100,
    message: "Video ready!",
  });

  return { videoBlob, objectUrl, hasAudio: hasAnyAudio, totalDurationMs };
}
