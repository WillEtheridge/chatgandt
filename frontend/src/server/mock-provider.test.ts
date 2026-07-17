import { describe, expect, it } from "vitest";
import { isModelOutcome } from "@/lib/chatgnt-contract";
import { MockChatGntProvider } from "@/server/mock-provider";

describe("mock provider", () => {
  it("returns a contract-valid Spirit Guide result", async () => {
    expect(isModelOutcome(await new MockChatGntProvider().generateSpiritGuide())).toBe(true);
  });

  it("returns two answers and a valid reveal mapping", async () => {
    const result = await new MockChatGntProvider().generateTasting();
    expect(isModelOutcome(result.answers[1])).toBe(true);
    expect(isModelOutcome(result.answers[2])).toBe(true);
    expect([1, 2]).toContain(result.fineTunedAnswer);
  });
});
