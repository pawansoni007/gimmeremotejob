# extension — Wellfound Apply Assistant (Chrome, MV3)

React + **TypeScript 7.0** (native preview `tsgo`), Radix UI, core-js. Built with
Vite + `@crxjs/vite-plugin`.

## Develop

```bash
npm install
npm run dev        # Vite dev build into dist/
npm run typecheck  # tsgo --noEmit  (TypeScript 7.0 native)
```

Then load it in Chrome: `chrome://extensions` → enable **Developer mode** →
**Load unpacked** → select the `dist/` folder.

## Layout

- `src/content/` — content script + the **stable Wellfound selectors**
  (`selectors.ts`). We anchor on `data-test` / `id` / `name` / `href`, never the
  hashed `styles_*` classes. Reading the job (Step 2) and questions (Step 3) go here.
- `src/panel/` — the side-panel UI (Claude-styled). Streams the agent log +
  suggested answers (Step 5).
- `src/background/` — service worker; opens the side panel.

> Step 1 = skeleton. Content script currently just detects the job modal and logs.
