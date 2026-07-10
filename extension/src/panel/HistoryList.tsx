import { useEffect, useState } from "react";
import { type ConversationSummary, describeFetchError, fetchConversations } from "./api";

// Past drafting runs, newest first. Click one to reopen and continue it.
export function HistoryList({ onOpen }: { onOpen: (id: string) => void }) {
  const [items, setItems] = useState<ConversationSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConversations()
      .then(setItems)
      .catch((err) => setError(describeFetchError(err)));
  }, []);

  if (error) return <div className="error-note">{error}</div>;
  if (items === null) return <p className="card-note">Loading history…</p>;
  if (items.length === 0) {
    return (
      <div className="empty-state">
        <p>No saved drafts yet.</p>
        <p className="hint">Draft answers for a job and it will be remembered here.</p>
      </div>
    );
  }

  return (
    <ul className="history-list">
      {items.map((item) => (
        <li key={item.id}>
          <button className="history-item" onClick={() => onOpen(item.id)}>
            <span className="history-title">{item.title}</span>
            <span className="history-sub">
              {item.company} · {item.questionCount}{" "}
              {item.questionCount === 1 ? "question" : "questions"} · {item.status}
            </span>
            <span className="history-when">{new Date(item.updatedAt).toLocaleString()}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
