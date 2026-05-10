import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Pin root/cache so resolution does not wander to a parent `node_modules` (e.g. under your user folder).
export default defineConfig({
  root: __dirname,
  cacheDir: path.join(__dirname, "node_modules", ".vite"),
  plugins: [react()],
  server: {
    // dev only — proxies /api to local backend
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
