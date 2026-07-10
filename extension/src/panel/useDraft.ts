import { useCallback, useEffect, useRef, useState } from "react";
import { splitAnswers } from "../shared/answers";
import type { JobInfo } from "../shared/types";
import { describeFetchError, streamSse } from "./api";

// Drives one drafting run against the service: POST the job, stream the SSE
// events, expose live text while it streams and per-question answers when done.
// (EventSource can't POST, so api.streamSse parses the stream off fetch().)

export type DraftStatus = "idle" | "streaming" | "done" | "error";

export interface DraftState {
  status: DraftStatus;
  /** Raw assistant text so far (streaming) / final text (done). */
  liveText: string;
  /** One entry per question once done; null before that. */
  answers: string[] | null;
  error: string | null;
  /** Set when the run was persisted — the id to find it under History. */
  conversationId: string | null;
}

const IDLE: DraftState = {
  status: "idle",
  liveText: "",
  answers: null,
  error: null,
  conversationId: null,
};

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
    setState({ ...IDLE, status: "streaming" });

    let live = "";
    let finalText = "";
    let errorMessage: string | null = null;
    let conversationId: string | null = null;

    try {
      await streamSse(
        "/apply/stream",
        currentJob,
        (event) => {
          if (event.type === "text_delta" && event.text) {
            live += event.text;
            const liveText = live;
            setState((s) => ({ ...s, liveText }));
          } else if (event.type === "turn_complete" && typeof event.text === "string") {
            finalText = event.text;
          } else if (event.type === "saved") {
            conversationId = event.conversation_id ?? null;
          } else if (event.type === "error" && !finalText) {
            errorMessage = event.message ?? "unknown error";
          }
        },
        controller.signal,
      );

      if (finalText) {
        setState({
          status: "done",
          liveText: finalText,
          answers: splitAnswers(finalText, currentJob.questions.length),
          error: null,
          conversationId,
        });
      } else {
        setState({
          ...IDLE,
          status: "error",
          liveText: live,
          error: errorMessage ?? "The stream ended without a draft.",
        });
      }
    } catch (err) {
      if (controller.signal.aborted) {
        setState(IDLE);
        return;
      }
      setState({ ...IDLE, status: "error", liveText: live, error: describeFetchError(err) });
    }
  }, []);

  return { state, start, stop };
}
