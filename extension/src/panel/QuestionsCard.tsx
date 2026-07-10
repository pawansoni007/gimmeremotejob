import type { JobInfo } from "../shared/types";

// The Apply form's written questions. Each question gets an answer slot that
// the agent fills in Step 5 — for now we show the question, its length hint,
// and anything the user already typed in the real form.
export function QuestionsCard({ job }: { job: JobInfo }) {
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

  return (
    <section className="questions-card">
      <h2 className="card-heading">
        Apply questions
        <span className="count-badge">{job.questions.length}</span>
      </h2>
      <ol className="question-list">
        {job.questions.map((q, i) => (
          <li className="question-item" key={q.id}>
            <div className="question-top">
              <span className="q-num">Q{i + 1}</span>
              <span className="q-kind">
                {q.kind === "textarea" ? "long answer" : "short answer"}
              </span>
            </div>
            <p className="q-text">{q.question}</p>
            {q.currentValue && (
              <p className="q-draft">
                <span className="q-draft-label">Already typed:</span> {q.currentValue}
              </p>
            )}
          </li>
        ))}
      </ol>
      <p className="card-note">Drafted answers land here in Step 5.</p>
    </section>
  );
}
