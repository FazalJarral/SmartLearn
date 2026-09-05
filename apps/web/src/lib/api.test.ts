import { describe, expect, it } from "vitest";

import { documentStatusSchema } from "./api";

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
