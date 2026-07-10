import type { ContentMessage } from "../shared/types";
import { CURRENT_JOB_KEY } from "../shared/types";

// Service worker. The toolbar icon opens the side panel, and we relay job data
// from the content script into chrome.storage.session — the panel can't receive
// runtime messages it wasn't open for, but storage + onChanged gives it both
// the current value on open and live updates after.

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel?.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {
    /* sidePanel API unavailable — ignore */
  });
});

chrome.runtime.onMessage.addListener((message: ContentMessage) => {
  if (message.type === "JOB_UPDATED") {
    void chrome.storage.session.set({ [CURRENT_JOB_KEY]: message.job });
  } else if (message.type === "JOB_CLEARED") {
    void chrome.storage.session.remove(CURRENT_JOB_KEY);
  }
});
