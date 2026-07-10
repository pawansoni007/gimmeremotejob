import type { JobInfo } from "../shared/types";
import { CopyButton } from "./CopyButton";
import { useDraft } from "./useDraft";

// The Apply form's written questions, and the drafting flow: hit "Draft
// answers", watch the agent stream, then copy each answer into the real form.
// Saved runs land in History; onSaved jumps straight to the conversation.
export function QuestionsCard({
  job,
  onSaved,
}: {
  job: JobInfo;
  onSaved?: (conversationId: string) => void;
}) {
  const { state, start, stop } = useDraft(job);

  if (!job.hasApplyForm) {
    return (
      <section className="questions-card">
        <h2 className="card-heading">Apply questions</h2>
        <p className="card-note">
          No apply form in this modal — this job likely takes applications on the
          company&apos;s site{job.emails.length > 0 ? " or by email" : ""}.
        </p>
      </section>
    );
  }

  if (job.questions.length === 0) {
    return (
      <section className="questions-card">
        <h2 className="card-heading">Apply questions</h2>
        <p className="card-note">
          The Apply form has no written questions — you can apply directly.
        </p>
      </section>
    );
  }

  const streaming = state.status === "streaming";

  return (
    <section className="questions-card">
      <div className="card-heading-row">
        <h2 className="card-heading">
          Apply questions
          <span className="count-badge">{job.questions.length}</span>
        </h2>
        {streaming ? (
          <button className="stop-button" onClick={stop}>
            Stop
          </button>
        ) : (
          <button className="draft-button" onClick={start}>
            {state.status === "done" || state.status === "error" ? "Redraft" : "Draft answers"}
          </button>
        )}
      </div>

      {streaming && (
        <div className="agent-log">
          {state.liveText ? (
            <p className="agent-text streaming">{state.liveText}</p>
          ) : (
            <p className="agent-thinking">Thinking…</p>
          )}
        </div>
      )}

      {state.status === "error" && (
        <div className="error-note">
          {state.error}
          {state.liveText && (
            <details className="error-partial">
              <summary>Partial output</summary>
              <p className="agent-text">{state.liveText}</p>
            </details>
          )}
        </div>
      )}

      <ol className="question-list">
        {job.questions.map((q, i) => {
          const answer = state.answers?.[i];
          return (
            <li className="question-item" key={q.id}>
              <div className="question-top">
                <span className="q-num">Q{i + 1}</span>
                <span className="q-kind">
                  {q.kind === "textarea" ? "long answer" : "short answer"}
                </span>
              </div>
              <p className="q-text">{q.question}</p>
              {q.currentValue && !answer && (
                <p className="q-draft">
                  <span className="q-draft-label">Already typed:</span> {q.currentValue}
                </p>
              )}
              {answer !== undefined && (
                <div className="answer-block">
                  {answer ? (
                    <>
                      <p className="answer-text">{answer}</p>
                      <div className="answer-actions">
                        <CopyButton text={answer} />
                      </div>
                    </>
                  ) : (
                    <p className="card-note">No answer drafted for this one — hit Redraft.</p>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ol>

      {state.status === "idle" && (
        <p className="card-note">
          Drafts stream from your local model — review, tweak, then copy into the form.
        </p>
      )}

      {state.status === "done" && state.conversationId && (
        <p className="card-note">
          Saved ✓{" "}
          <button
            className="link-button"
            onClick={() => onSaved?.(state.conversationId!)}
          >
            Continue this conversation
          </button>
        </p>
      )}
    </section>
  );
}
