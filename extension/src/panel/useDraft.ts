import { useCallback, useEffect, useRef, useState } from "react";
import { SseDecoder, splitAnswers } from "../shared/answers";
import { SERVICE_URL } from "../shared/config";
import type { JobInfo } from "../shared/types";

// Drives one drafting run against the service: POST the job, stream the SSE
// events, expose live text while it streams and per-question answers when done.
// (EventSource can't POST, so this parses the stream off fetch() by hand.)

export type DraftStatus = "idle" | "streaming" | "done" | "error";

export interface DraftState {
  status: DraftStatus;
  /** Raw assistant text so far (streaming) / final text (done). */
  liveText: string;
  /** One entry per question once done; null before that. */
  answers: string[] | null;
  error: string | null;
}

const IDLE: DraftState = { status: "idle", liveText: "", answers: null, error: null };

export function useDraft(job: JobInfo | null): {
  state: DraftState;
  start: () => void;
  stop: () => void;
} {
  const [state, setState] = useState<DraftState>(IDLE);
  const abortRef = useRef<AbortController | null>(null);
  const jobRef = useRef(job);
  jobRef.current = job;

  // A different job (not just a re-read of the same one) resets the draft.
  const jobKey = job?.jobId ?? job?.jobUrl ?? job?.title ?? null;
  useEffect(() => {
    abortRef.current?.abort();
    setState(IDLE);
  }, [jobKey]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const start = useCallback(async () => {
    const currentJob = jobRef.current;
    if (!currentJob) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setState({ status: "streaming", liveText: "", answers: null, error: null });

    let live = "";
    let finalText = "";
    let errorMessage: string | null = null;

    try {
      const response = await fetch(`${SERVICE_URL}/apply/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentJob),
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(`service responded ${response.status}`);
      }

      const reader = response.body.getReader();
      const textDecoder = new TextDecoder();
      const sse = new SseDecoder();

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const event of sse.push(textDecoder.decode(value, { stream: true }))) {
          if (event.type === "text_delta" && event.text) {
            live += event.text;
            const liveText = live;
            setState((s) => ({ ...s, liveText }));
          } else if (event.type === "turn_complete" && typeof event.text === "string") {
            finalText = event.text;
          } else if (event.type === "error" && !finalText) {
            errorMessage = event.message ?? "unknown error";
          }
        }
      }

      if (finalText) {
        setState({
          status: "done",
          liveText: finalText,
          answers: splitAnswers(finalText, currentJob.questions.length),
          error: null,
        });
      } else {
        setState({
          status: "error",
          liveText: live,
          answers: null,
          error: errorMessage ?? "The stream ended without a draft.",
        });
      }
    } catch (err) {
      if (controller.signal.aborted) {
        setState(IDLE);
        return;
      }
      // fetch() rejects with TypeError when nothing is listening.
      const message =
        err instanceof TypeError
          ? `Can't reach the service at ${SERVICE_URL}. Start it with: cd service && uv run uvicorn app.main:app --port 8756`
          : String(err);
      setState({ status: "error", liveText: live, answers: null, error: message });
    }
  }, []);

  return { state, start, stop };
}
