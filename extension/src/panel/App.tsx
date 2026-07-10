import { JobCard } from "./JobCard";
import { useCurrentJob } from "./useCurrentJob";

export function App() {
  const job = useCurrentJob();

  return (
    <main className="panel">
      <header className="panel-header">
        <h1>Apply Assistant</h1>
      </header>

      {job ? (
        <JobCard job={job} />
      ) : (
        <div className="empty-state">
          <p>No job in view.</p>
          <p className="hint">
            Open a job on wellfound.com and it will show up here — questions and
            drafted answers land in the next steps.
          </p>
        </div>
      )}
    </main>
  );
}
