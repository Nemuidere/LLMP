import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Backend host: "backend" when running inside docker-compose, "localhost"
// when running vite on the host.
const BACKEND = process.env.VITE_BACKEND_HOST ?? "localhost";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: `http://${BACKEND}:8000`,
        changeOrigin: true,
      },
    },
  },
});
