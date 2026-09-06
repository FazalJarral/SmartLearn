import { describe, expect, it } from "vitest";

import { documentStatusSchema, getApiBaseUrl } from "./api";

describe("documentStatusSchema", () => {
  it("accepts a valid status response", () => {
    const parsed = documentStatusSchema.parse({
      document_id: "9c798477-6cff-473f-b76a-0de947d8d0a7",
      stage: "content_ready",
      progress: 70,
      message: "Ready",
      error_code: null,
      package_id: null,
    });
    expect(parsed.progress).toBe(70);
  });
});

describe("getApiBaseUrl", () => {
  it("adds the api version prefix when Render root is configured", () => {
    expect(getApiBaseUrl("https://smartlearn-vpiy.onrender.com")).toBe(
      "https://smartlearn-vpiy.onrender.com/api/v1",
    );
  });

  it("keeps an existing api version prefix", () => {
    expect(getApiBaseUrl("https://smartlearn-vpiy.onrender.com/api/v1/")).toBe(
      "https://smartlearn-vpiy.onrender.com/api/v1",
    );
  });
});
