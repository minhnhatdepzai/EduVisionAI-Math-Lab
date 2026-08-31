import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "./api.js";

describe("Math Vision Lab API", () => {
  beforeEach(() => {
    const values = new Map([["smartclassroom.accessToken", "teacher-token"]]);
    vi.stubGlobal("localStorage", {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, String(value)),
      removeItem: (key) => values.delete(key),
    });
    vi.stubGlobal("window", {
      dispatchEvent: vi.fn(),
      location: { origin: "https://localhost:8443" },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("sends a new text problem to the structured analysis endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ questions: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));
    vi.stubGlobal("fetch", fetchMock);

    await api.mathLab.analyzeText("Một đề mới", 5);

    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/math-lab/analyze/text");
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      text: "Một đề mới",
      grade_hint: 5,
    });
    expect(fetchMock.mock.calls[0][1].headers.get("Authorization")).toBe("Bearer teacher-token");
  });

  it("uploads the original image bytes with browser-managed multipart headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ questions: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));
    vi.stubGlobal("fetch", fetchMock);
    const file = new File([new Uint8Array([0xff, 0xd8, 0xff])], "de-toan.jpg", {
      type: "image/jpeg",
    });

    await api.mathLab.analyzeImage(file, 4);

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/v1/math-lab/analyze/image");
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get("file").name).toBe("de-toan.jpg");
    expect(options.body.get("grade_hint")).toBe("4");
    expect(options.headers.has("Content-Type")).toBe(false);
  });
});
