import { SseDecoder, type StreamEventData } from "../shared/answers";
import { SERVICE_URL } from "../shared/config";
import type { ApplyQuestion, JobInfo } from "../shared/types";

// Talking to the local service: SSE streaming + the history endpoints.

/** POST a body and feed each decoded SSE event to the handler. */
export async function streamSse(
  path: string,
  body: unknown,
  onEvent: (event: StreamEventData) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(`${SERVICE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`service responded ${response.status}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const sse = new SseDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    for (const event of sse.push(decoder.decode(value, { stream: true }))) {
      onEvent(event);
    }
  }
}

/** The friendly variant of fetch-failed for this service. */
export function describeFetchError(err: unknown): string {
  return err instanceof TypeError
    ? `Can't reach the service at ${SERVICE_URL}. Start it with: cd service && uv run uvicorn app.main:app --port 8756`
    : String(err);
}

export interface ConversationSummary {
  id: string;
  title: string;
  company: string;
  jobUrl: string | null;
  status: string;
  questionCount: number;
  updatedAt: string;
}

export interface ConversationDetail {
  id: string;
  model: string;
  /** The JobPayload as originally captured (same shape as JobInfo). */
  job: Partial<JobInfo> & { title: string };
  questions: ApplyQuestion[];
  answers: Record<string, string>;
  status: string;
  messages: { role: string; text: string }[];
  updatedAt: string;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${SERVICE_URL}${path}`);
  if (!response.ok) throw new Error(`service responded ${response.status}`);
  return (await response.json()) as T;
}

export function fetchConversations(): Promise<ConversationSummary[]> {
  return getJson("/conversations");
}

export function fetchConversation(id: string): Promise<ConversationDetail> {
  return getJson(`/conversations/${id}`);
}
