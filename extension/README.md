# extension — Wellfound Apply Assistant (Chrome, MV3)

React + **TypeScript 7.0** (native preview `tsgo`), Radix UI, core-js. Built with
Vite + `@crxjs/vite-plugin`.

## Develop

```bash
npm install
npm run dev        # Vite dev build into dist/
npm run typecheck  # tsgo --noEmit  (TypeScript 7.0 native)
npm run test:unit  # pure-logic tests (SSE decoding, answer splitting) in Node
npm run test:dom   # extraction test against a saved real job modal (headless Chrome)
```

Then load it in Chrome: `chrome://extensions` → enable **Developer mode** →
**Load unpacked** → select the `dist/` folder.

`test:dom` launches your installed Chrome via `playwright-core`; set
`CHROMIUM_PATH=/path/to/chromium` if it can't find one.

## Layout

- `src/content/` — content script. `selectors.ts` holds the **stable Wellfound
  anchors** (`data-test` / `id` / `name` / `href` — never the hashed `styles_*`
  classes), `extract.ts` turns the open job modal into a `JobInfo`, and
  `content.ts` watches the SPA for the modal appearing/changing/closing
  (debounced MutationObserver + diff, since the modal's content streams in
  after it mounts).
- `src/shared/` — the `JobInfo` type + messages shared by all three contexts.
- `src/background/` — service worker; opens the side panel and relays job data
  from the content script into `chrome.storage.session`.
- `src/panel/` — the side-panel UI (Claude-styled). Shows the current job now;
  questions + streamed answers land in Steps 3–5.
- `test/` — DOM test running `extract.ts` against `fixtures/job-modal.html`
  (a saved copy of a real job modal) in headless Chromium.

## How the data flows (Step 2)

```
wellfound.com DOM ──content script──► chrome.runtime message
        ──background──► chrome.storage.session ──onChanged──► side panel
```

Storage (not direct messaging) is the bus so the panel shows the job even when
it's opened *after* the job was captured.

> Steps 1–5 done: the panel shows the job and its Apply questions, and **Draft
> answers** streams the model's draft live from the local service
> (`POST /apply/stream`, SSE over fetch — EventSource can't POST), then splits
> it into per-question answers with Copy buttons. The service must be running
> (`cd service && uv run uvicorn app.main:app --port 8756`); the panel says so
> if it isn't.
