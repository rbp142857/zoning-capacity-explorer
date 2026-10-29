import { defineConfig } from "vite";

export default defineConfig({
  // Relative asset paths, so the built site works at any URL path
  // (GitHub Pages serves it at /<repo-name>/, not at /).
  base: "./",
  server: { port: 5173 },
  // MapLibre itself is ~800 kB minified (~230 kB gzipped); that is expected.
  build: { chunkSizeWarningLimit: 900 },
});
