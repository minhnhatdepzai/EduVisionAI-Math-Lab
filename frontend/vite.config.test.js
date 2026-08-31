import { afterEach, describe, expect, it, vi } from "vitest";

import createViteConfig from "./vite.config.js";

describe("frontend port configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses separate configurable ports for Vite and the public ingress proxy", () => {
    vi.stubEnv("VITE_FRONTEND_HTTPS", "false");
    vi.stubEnv("VITE_FRONTEND_PORT", "5174");
    vi.stubEnv("PUBLIC_HTTPS_PORT", "9443");

    const config = createViteConfig({ command: "serve", mode: "test" });

    expect(config.server.port).toBe(5174);
    expect(config.preview.port).toBe(5174);
    expect(config.server.proxy["/api"].target).toBe("https://localhost:9443");
    expect(config.server.proxy["/health"].target).toBe(
      "https://localhost:9443",
    );
  });

  it.each([
    ["VITE_FRONTEND_PORT", "0"],
    ["VITE_FRONTEND_PORT", "65536"],
    ["PUBLIC_HTTPS_PORT", "not-a-port"],
  ])("rejects invalid %s values", (variableName, value) => {
    vi.stubEnv("VITE_FRONTEND_HTTPS", "false");
    vi.stubEnv(variableName, value);

    expect(() =>
      createViteConfig({ command: "serve", mode: "test" }),
    ).toThrow(`${variableName} must be a number between 1 and 65535.`);
  });
});
