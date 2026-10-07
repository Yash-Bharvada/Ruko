import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from "vite-tsconfig-paths";
import { nitro } from "nitro/vite";

export default defineConfig(({ command }) => ({
  plugins: [
    tsConfigPaths({ projects: ["./tsconfig.json"] }),
    tanstackStart({
      server: { entry: "server" },
    }),
    react(),
    tailwindcss(),
    command === "build" ? nitro({ defaultPreset: "cloudflare-module" }) : undefined,
  ].filter(Boolean),
  server: {
    port: 3000,
    proxy: {
      "/v1": {
        target: "http://localhost:8000",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("error", (_err, _req, res) => {
            if ("writeHead" in res && !res.headersSent) {
              res.writeHead(503, { "Content-Type": "application/json" });
              res.end(
                JSON.stringify({
                  error: {
                    code: "BACKEND_OFFLINE",
                    message:
                      "Ruko backend on http://localhost:8000 is not reachable. Run: cd backend && python -m uvicorn app.main:app --reload --port 8000",
                  },
                }),
              );
            }
          });
        },
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("error", (_err, _req, res) => {
            if ("writeHead" in res && !res.headersSent) {
              res.writeHead(503, { "Content-Type": "application/json" });
              res.end(
                JSON.stringify({
                  status: "offline",
                  error: "Backend not reachable on port 8000",
                }),
              );
            }
          });
        },
      },
    },
  },
}));
