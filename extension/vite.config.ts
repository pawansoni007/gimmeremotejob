import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { crx } from "@crxjs/vite-plugin";
import manifest from "./manifest.json";

// Build the MV3 extension. @crxjs lets the manifest reference .ts/.tsx/.html
// source paths directly and handles bundling them.
export default defineConfig({
  plugins: [react(), crx({ manifest })],
});
