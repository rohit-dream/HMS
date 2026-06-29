import { describe, expect, it } from "vitest";
import { normalizeEtag } from "./opd";

describe("normalizeEtag", () => {
  it("strips surrounding quotes", () => {
    expect(normalizeEtag('"abc123"')).toBe("abc123");
  });

  it("returns null for empty values", () => {
    expect(normalizeEtag(undefined)).toBeNull();
    expect(normalizeEtag("")).toBeNull();
  });
});
