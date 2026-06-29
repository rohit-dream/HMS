import { describe, expect, it } from "vitest";
import { opdQueuePriorityLabel, opdQueueStatusLabel } from "./queueFormatters";

describe("opdQueueStatusLabel", () => {
  it("maps known queue statuses", () => {
    expect(opdQueueStatusLabel("waiting")).toBe("Waiting");
    expect(opdQueueStatusLabel("in_consultation")).toBe("In consultation");
    expect(opdQueueStatusLabel("skipped")).toBe("Skipped");
  });
});

describe("opdQueuePriorityLabel", () => {
  it("maps known priorities", () => {
    expect(opdQueuePriorityLabel("normal")).toBe("Normal");
    expect(opdQueuePriorityLabel("emergency")).toBe("Emergency");
  });
});
