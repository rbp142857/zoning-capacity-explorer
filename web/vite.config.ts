/// <reference types="vitest" />
import { defineConfig } from "vite";

export default defineConfig({
  // Relative asset paths, so the built site works at any URL path
  // (GitHub Pages serves it at /<repo-name>/, not at /).
  base: "./",
  server: { port: 5173 },
  // MapLibre itself is ~800 kB minified (~230 kB gzipped); that is expected.
  build: { chunkSizeWarningLimit: 900 },
  // Only our own tests (not the ones shipped inside node_modules).
  test: {
    include: ["src/**/*.test.ts"],
    // node_modules is a link to node_modules.nosync (keeps iCloud from
    // syncing it); tell Vitest that folder holds installed packages too.
    deps: { moduleDirectories: ["node_modules", "node_modules.nosync"] },
  },
});
