import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // In development the Vite server proxies API calls to Django, so the browser sees a
    // single origin — exactly like production, where nginx does the same job.
    proxy: {
      "/api": "http://localhost:8000",
      "/admin": "http://localhost:8000",
      "/static": "http://localhost:8000",
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Vendor chunks change rarely, so browsers keep them cached across deploys.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          query: ["@tanstack/react-query", "axios"],
          charts: ["recharts"],
        },
      },
    },
  },
  test: {
    environment: "node",
  },
});
