import { describe, expect, it } from "vitest";
import {
  isChatGntRecipe,
  parseSpiritGuideResponse,
  parseTastingRoomResponse,
  type ModelOutcome,
} from "@/lib/chatgnt-contract";

const recipe = {
  title: "The Test Pour",
  ingredients: [
    { amount: 50, unit: "ml", name: "useful answer" },
    { amount: 25, unit: "ml", name: "clear structure" },
    { amount: 1, unit: "dash", name: "wit" },
  ],
  method: ["Mix the evidence.", "Serve the conclusion."],
  garnish: "One concrete next step.",
};

const outcome: ModelOutcome = { status: "valid", recipe };

describe("ChatG&T browser contract", () => {
  it("accepts an exact valid recipe", () => {
    expect(isChatGntRecipe(recipe)).toBe(true);
  });

  it("rejects extra recipe fields", () => {
    expect(isChatGntRecipe({ ...recipe, commentary: "no" })).toBe(false);
  });

  it("requires the expected request identity", () => {
    expect(() =>
      parseSpiritGuideResponse({ schemaVersion: 1, requestId: "other", outcome }, "expected"),
    ).toThrow(/Spirit Guide/);
  });

  it("accepts JSON string keys for tasting answers", () => {
    const parsed = parseTastingRoomResponse(
      { schemaVersion: 1, requestId: "request", answers: { "1": outcome, "2": outcome }, fineTunedAnswer: 2 },
      "request",
    );
    expect(parsed.fineTunedAnswer).toBe(2);
  });
});
