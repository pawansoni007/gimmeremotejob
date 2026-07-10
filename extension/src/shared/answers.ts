// Pure logic for Step 5's streaming: decoding the service's SSE bytes and
// splitting the drafted text into per-question answers. No DOM, no chrome.*,
// so test/answers.test.mjs can run this directly in Node.

/** One JSON event off the wire (see service openharness_runner.event_to_dict). */
export interface StreamEventData {
  type: string;
  text?: string;
  message?: string;
  recoverable?: boolean;
  usage?: { input_tokens: number; output_tokens: number };
  /** On {"type": "saved"} — the persisted conversation's id. */
  conversation_id?: string;
}

/**
 * Incremental SSE decoder. Feed it raw chunks as they arrive; it returns the
 * completed `data:` events, buffering partials across chunk boundaries and
 * ignoring comments/pings and non-JSON lines. Line endings are normalized —
 * sse-starlette sends \r\n — including a \r\n split across two chunks.
 */
export class SseDecoder {
  private buf = "";
  /** A trailing \r held back in case the next chunk starts with \n. */
  private pendingCr = "";

  push(chunk: string): StreamEventData[] {
    let data = this.pendingCr + chunk;
    this.pendingCr = "";
    if (data.endsWith("\r")) {
      this.pendingCr = "\r";
      data = data.slice(0, -1);
    }
    this.buf += data.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const events: StreamEventData[] = [];

    let sep: number;
    while ((sep = this.buf.indexOf("\n\n")) >= 0) {
      const block = this.buf.slice(0, sep);
      this.buf = this.buf.slice(sep + 2);

      const dataLines = block
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice("data:".length).trimStart());
      if (dataLines.length === 0) continue;

      try {
        events.push(JSON.parse(dataLines.join("\n")) as StreamEventData);
      } catch {
        // Malformed event — skip rather than kill the stream.
      }
    }
    return events;
  }
}

/**
 * Split the model's final text into one answer per question, keyed off the
 * `### Answer <n>` headings the system prompt demands. Missing sections stay
 * empty; with no headings at all, the whole text becomes answer 1 (the model
 * mostly follows the contract, but a single-question drift shouldn't lose the
 * draft).
 */
export function splitAnswers(text: string, questionCount: number): string[] {
  const answers: string[] = Array.from({ length: questionCount }, () => "");
  const headings = [...text.matchAll(/^###\s*Answer\s+(\d+)\s*$/gim)];

  if (headings.length === 0) {
    if (questionCount > 0) answers[0] = text.trim();
    return answers;
  }

  headings.forEach((match, i) => {
    const n = Number(match[1]);
    if (n < 1 || n > questionCount) return;
    const start = (match.index ?? 0) + match[0].length;
    const end = i + 1 < headings.length ? headings[i + 1].index : text.length;
    answers[n - 1] = text.slice(start, end).trim();
  });

  return answers;
}
