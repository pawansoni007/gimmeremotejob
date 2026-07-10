import { SELECTORS } from "./selectors";

// Step 1 stub. Wellfound is a single-page app, so the job opens as a slide-in
// modal with no page reload. We watch the DOM and react when that modal appears.
// Extracting the job fields (Step 2) and the Apply questions (Step 3) happens here.

function onModalOpen(modal: HTMLElement): void {
  // eslint-disable-next-line no-console
  console.debug("[apply-assistant] job modal detected", modal);
  // TODO(Step 2): read title, company, salary, skills, #job-description, job id.
  // TODO(Step 3): read [name^="customQuestionAnswers"] fields + their <label> text.
}

const observer = new MutationObserver(() => {
  const modal = document.querySelector<HTMLElement>(SELECTORS.modal);
  if (modal && !modal.dataset.applyAssistantSeen) {
    modal.dataset.applyAssistantSeen = "1";
    onModalOpen(modal);
  }
});

observer.observe(document.body, { childList: true, subtree: true });
