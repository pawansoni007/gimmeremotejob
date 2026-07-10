import { resolve } from "node:path";
import { defineConfig } from "vite";

// Bundles the content-script extraction logic as a browser global (window.WF)
// so the DOM test can inject it into a real Chromium page. Output goes to
// dist-test/ (gitignored), separate from the extension build in dist/.
export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "../src/content/extract.ts"),
      name: "WF",
      formats: ["iife"],
      fileName: () => "extract.iife.js",
    },
    outDir: resolve(__dirname, "../dist-test"),
    emptyOutDir: true,
  },
});
