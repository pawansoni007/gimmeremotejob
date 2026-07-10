import { useState } from "react";
import { ConversationView } from "./ConversationView";
import { HistoryList } from "./HistoryList";
import { JobCard } from "./JobCard";
import { QuestionsCard } from "./QuestionsCard";
import { useCurrentJob } from "./useCurrentJob";

type View = { kind: "live" } | { kind: "history" } | { kind: "conversation"; id: string };

export function App() {
  const job = useCurrentJob();
  const [view, setView] = useState<View>({ kind: "live" });

  return (
    <main className="panel">
      <header className="panel-header-row">
        <h1>Apply Assistant</h1>
        {view.kind === "live" ? (
          <button className="nav-button" onClick={() => setView({ kind: "history" })}>
            History
          </button>
        ) : (
          <button
            className="nav-button"
            onClick={() =>
              setView(view.kind === "conversation" ? { kind: "history" } : { kind: "live" })
            }
          >
            ← Back
          </button>
        )}
      </header>

      {view.kind === "history" && <HistoryList onOpen={(id) => setView({ kind: "conversation", id })} />}
      {view.kind === "conversation" && <ConversationView id={view.id} />}
      {view.kind === "live" &&
        (job ? (
          <>
            <QuestionsCard job={job} onSaved={(id) => setView({ kind: "conversation", id })} />
            <JobCard job={job} />
          </>
        ) : (
          <div className="empty-state">
            <p>No job in view.</p>
            <p className="hint">
              Open a job on wellfound.com and it will show up here — or check History
              for past drafts.
            </p>
          </div>
        ))}
    </main>
  );
}
