import { useCallback, useEffect, useRef, useState } from "react";
import { CopyButton } from "./CopyButton";
import {
  type ConversationDetail,
  describeFetchError,
  fetchConversation,
  streamSse,
} from "./api";

// A saved conversation, reopened: the drafted answers (copyable) plus a
// follow-up box that resumes the same conversation — the model sees its own
// earlier draft and revises it.
export function ConversationView({ id }: { id: string }) {
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [followup, setFollowup] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [liveText, setLiveText] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(() => {
    fetchConversation(id)
      .then((d) => {
        setDetail(d);
        setError(null);
      })
      .catch((err) => setError(describeFetchError(err)));
  }, [id]);

  useEffect(() => {
    load();
    return () => abortRef.current?.abort();
  }, [load]);

  const send = useCallback(async () => {
    const message = followup.trim();
    if (!message || streaming) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setStreaming(true);
    setLiveText("");
    setError(null);

    let errorMessage: string | null = null;
    try {
      await streamSse(
        `/conversations/${id}/messages/stream`,
        { message },
        (event) => {
          if (event.type === "text_delta" && event.text) {
            setLiveText((t) => t + event.text);
          } else if (event.type === "error") {
            errorMessage = event.message ?? "unknown error";
          }
        },
        controller.signal,
      );
      if (errorMessage) setError(errorMessage);
      else setFollowup("");
      load(); // pick up the updated answers + transcript
    } catch (err) {
      if (!controller.signal.aborted) setError(describeFetchError(err));
    } finally {
      setStreaming(false);
      setLiveText("");
    }
  }, [followup, streaming, id, load]);

  if (error && !detail) return <div className="error-note">{error}</div>;
  if (!detail) return <p className="card-note">Loading conversation…</p>;

  // The transcript minus the opening prompt (the whole job posting — noise)
  // and the first draft (already shown as the answers below).
  const followups = detail.messages.slice(2);

  return (
    <div>
      <section className="questions-card">
        <h2 className="card-heading">{detail.job.title}</h2>
        <p className="card-note">
          {detail.job.company?.name ?? "Unknown company"} · {detail.status} ·{" "}
          {new Date(detail.updatedAt).toLocaleString()}
        </p>

        <ol className="question-list">
          {detail.questions.map((q, i) => {
            const answer = detail.answers[q.id] ?? "";
            return (
              <li className="question-item" key={q.id}>
                <div className="question-top">
                  <span className="q-num">Q{i + 1}</span>
                </div>
                <p className="q-text">{q.question}</p>
                {answer && (
                  <div className="answer-block">
                    <p className="answer-text">{answer}</p>
                    <div className="answer-actions">
                      <CopyButton text={answer} />
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </section>

      <section className="questions-card">
        <h2 className="card-heading">Continue this conversation</h2>

        {followups.length > 0 && (
          <div className="transcript">
            {followups.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>
                {m.text}
              </div>
            ))}
          </div>
        )}

        {streaming && (
          <div className="agent-log">
            {liveText ? (
              <p className="agent-text streaming">{liveText}</p>
            ) : (
              <p className="agent-thinking">Thinking…</p>
            )}
          </div>
        )}

        {error && detail && <div className="error-note">{error}</div>}

        <div className="followup-row">
          <textarea
            className="followup-input"
            rows={2}
            placeholder="e.g. make answer 1 shorter and more direct"
            value={followup}
            onChange={(e) => setFollowup(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            disabled={streaming}
          />
          <button className="draft-button" onClick={send} disabled={streaming || !followup.trim()}>
            {streaming ? "…" : "Send"}
          </button>
        </div>
      </section>
    </div>
  );
}
