import type { ContentMessage, JobInfo } from "../shared/types";
import { extractJob } from "./extract";
import { SELECTORS } from "./selectors";

// Wellfound is a single-page app: a job opens as a slide-in modal with no page
// reload, and its content (description, apply form) streams in after the modal
// mounts. So instead of a one-shot "modal appeared" hook, we re-extract on every
// (debounced) DOM change and only notify when the job data actually changed.
// That one loop handles: modal opening, content finishing loading, switching to
// another job, and the modal closing.

let lastSent: string | null = null;
let debounceTimer: number | undefined;

function send(message: ContentMessage): void {
  chrome.runtime.sendMessage(message).catch(() => {
    // Panel/worker not listening (e.g. extension reloaded) — fine, we'll resend
    // on the next change.
  });
}

/** Fingerprint for change detection — capturedAt would differ on every read. */
function fingerprint(job: JobInfo): string {
  return JSON.stringify({ ...job, capturedAt: 0 });
}

function tick(): void {
  const modal = document.querySelector<HTMLElement>(SELECTORS.modal);

  if (!modal) {
    if (lastSent !== null) {
      lastSent = null;
      send({ type: "JOB_CLEARED" });
    }
    return;
  }

  const job = extractJob(modal);
  // Still loading — no title yet means there's nothing worth showing.
  if (!job.title) return;

  const print = fingerprint(job);
  if (print === lastSent) return;
  lastSent = print;
  send({ type: "JOB_UPDATED", job });
}

const observer = new MutationObserver(() => {
  clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(tick, 250);
});

observer.observe(document.body, { childList: true, subtree: true });
tick(); // in case the modal is already open when the script loads
