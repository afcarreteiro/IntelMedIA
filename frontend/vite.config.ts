import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    fs: {
      allow: [".."],
    },
    proxy: {
      "/auth": "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    include: ["../tests/frontend/unit/**/*.test.ts"],
  },
});
