import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const assetsDir = path.resolve(rootDir, "assets");
const defaultGoogleClientId =
  "139504495012-t2vvo92n9k5m5d1b7ool5a1ve25ngeqa.apps.googleusercontent.com";

// Serve /assets/* from the local assets folder in dev and copy them on build.
function localAssets() {
  return {
    name: "smartclassroom-assets",
    configureServer(server) {
      server.middlewares.use("/assets", (request, response, next) => {
        const url = new URL(request.url || "/", "http://localhost");
        const relativePath = decodeURIComponent(url.pathname)
          .replace(/^\/assets\/?/, "")
          .replace(/^\/+/, "");
        const filePath = path.resolve(assetsDir, relativePath);
        if (!filePath.startsWith(`${assetsDir}${path.sep}`)) return next();

        fs.stat(filePath, (error, stats) => {
          if (error || !stats.isFile()) return next();
          response.setHeader("Content-Type", contentType(filePath));
          response.setHeader("Cache-Control", "no-store");
          fs.createReadStream(filePath).pipe(response);
        });
      });
    },
    writeBundle() {
      if (fs.existsSync(assetsDir)) {
        fs.cpSync(assetsDir, path.resolve(rootDir, "dist/assets"), { recursive: true });
      }
    },
  };
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return (
    {
      ".png": "image/png",
      ".webp": "image/webp",
      ".jpg": "image/jpeg",
      ".jpeg": "image/jpeg",
      ".svg": "image/svg+xml",
    }[ext] || "application/octet-stream"
  );
}

function parsePort(value, variableName) {
  const port = Number(value);

  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error(`${variableName} must be a number between 1 and 65535.`);
  }

  return port;
}

function enabled(value) {
  return ["1", "true", "yes", "on"].includes(String(value || "").trim().toLowerCase());
}

function tlsOptions(root, command, env) {
  const useHttps =
    command === "serve" && enabled(env.VITE_FRONTEND_HTTPS || "true");
  if (!useHttps) return undefined;

  const certFile = path.resolve(
    root,
    env.VITE_FRONTEND_TLS_CERT_FILE ||
      "../security/pki/dev/public-ingress/tls.crt",
  );
  const keyFile = path.resolve(
    root,
    env.VITE_FRONTEND_TLS_KEY_FILE ||
      "../security/pki/dev/public-ingress/tls.key",
  );

  if (!fs.existsSync(certFile) || !fs.existsSync(keyFile)) {
    throw new Error(
      "HTTPS certificate is missing. Run security/pki/scripts/generate-dev-public-ingress-cert.sh.",
    );
  }

  return {
    cert: fs.readFileSync(certFile),
    key: fs.readFileSync(keyFile),
  };
}

export default defineConfig(({ command, mode }) => {
  // Config evaluation does not automatically expose Vite .env values through
  // process.env. Loading every prefix keeps deployment values server-side;
  // only the explicit `define` entries below reach browser code.
  const env = loadEnv(mode, rootDir, "");
  const apiBaseUrl = env.API_BASE_URL || "/api/v1";
  const googleClientId =
    env.GOOGLE_CLIENT_ID || defaultGoogleClientId;
  const publicHttpsPort = parsePort(
    env.PUBLIC_HTTPS_PORT || "8443",
    "PUBLIC_HTTPS_PORT",
  );
  const backendTarget = (
    env.VITE_BACKEND_URL ||
    `https://localhost:${publicHttpsPort}`
  ).replace(/\/+$/, "");
  const frontendPort = parsePort(
    env.VITE_FRONTEND_PORT || "5173",
    "VITE_FRONTEND_PORT",
  );
  const https = tlsOptions(rootDir, command, env);
  const backendProxy = {
    target: backendTarget,
    changeOrigin: true,
    secure: true,
    ws: true,
  };

  return {
    plugins: [react(), localAssets()],
    // Only these two production values are explicitly compiled into browser
    // code. Other non-VITE environment variables remain server-side.
    define: {
      "import.meta.env.API_BASE_URL": JSON.stringify(apiBaseUrl),
      "import.meta.env.GOOGLE_CLIENT_ID": JSON.stringify(googleClientId),
    },
    server: {
      port: frontendPort,
      strictPort: true,
      https,
      proxy: {
        "/api": backendProxy,
        "/health": backendProxy,
        "/users": backendProxy,
        "/system": backendProxy,
      },
    },
    preview: {
      port: frontendPort,
      strictPort: true,
      https,
    },
  };
});
