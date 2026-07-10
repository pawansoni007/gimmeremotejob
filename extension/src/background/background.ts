// Service worker. For now it just makes the toolbar icon open the side panel.
chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel
    ?.setPanelBehavior({ openPanelOnActionClick: true })
    .catch(() => {
      /* sidePanel API unavailable — ignore in Step 1 */
    });
});
