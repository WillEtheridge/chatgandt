import type { ChatGntRecipe } from "@/components/recipe";

export const CHATGNT_SCHEMA_VERSION = 1 as const;
export const MAX_PROMPT_CHARACTERS = 500;

export type AnswerNumber = 1 | 2;
export type FailureKind = "invalid-json" | "invalid-schema" | "operational";

export type ModelOutcome =
  | { status: "valid"; recipe: ChatGntRecipe }
  | { status: "failure"; failure: FailureKind };

export type SpiritGuideResponse = {
  schemaVersion: typeof CHATGNT_SCHEMA_VERSION;
  requestId: string;
  outcome: ModelOutcome;
};

export type TastingRoomResponse = {
  schemaVersion: typeof CHATGNT_SCHEMA_VERSION;
  requestId: string;
  answers: Record<AnswerNumber, ModelOutcome>;
  fineTunedAnswer: AnswerNumber;
};

export type ApiErrorCode =
  | "invalid_request"
  | "rate_limited"
  | "provider_unavailable"
  | "provider_timeout"
  | "configuration_error";

export type ApiErrorResponse = {
  schemaVersion: typeof CHATGNT_SCHEMA_VERSION;
  requestId: string;
  error: { code: ApiErrorCode; message: string };
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && /\S/.test(value);
}

export function isChatGntRecipe(value: unknown): value is ChatGntRecipe {
  if (!isRecord(value) || !hasExactKeys(value, ["title", "ingredients", "method", "garnish"])) return false;
  if (!isNonEmptyString(value.title) || !isNonEmptyString(value.garnish)) return false;
  if (!Array.isArray(value.ingredients) || value.ingredients.length < 3 || value.ingredients.length > 8) return false;
  if (!Array.isArray(value.method) || value.method.length < 2 || value.method.length > 5) return false;
  if (!value.method.every(isNonEmptyString)) return false;
  return value.ingredients.every((ingredient) => {
    if (!isRecord(ingredient) || !hasExactKeys(ingredient, ["amount", "unit", "name"])) return false;
    return (
      typeof ingredient.amount === "number" &&
      Number.isFinite(ingredient.amount) &&
      ingredient.amount > 0 &&
      isNonEmptyString(ingredient.unit) &&
      isNonEmptyString(ingredient.name)
    );
  });
}

export function isModelOutcome(value: unknown): value is ModelOutcome {
  if (!isRecord(value) || value.status === undefined) return false;
  if (value.status === "valid") return hasExactKeys(value, ["status", "recipe"]) && isChatGntRecipe(value.recipe);
  if (value.status !== "failure" || !hasExactKeys(value, ["status", "failure"])) return false;
  return value.failure === "invalid-json" || value.failure === "invalid-schema" || value.failure === "operational";
}

export function parseSpiritGuideResponse(value: unknown, requestId?: string): SpiritGuideResponse {
  if (!isRecord(value) || !hasExactKeys(value, ["schemaVersion", "requestId", "outcome"])) {
    throw new TypeError("invalid Spirit Guide response envelope");
  }
  if (
    value.schemaVersion !== CHATGNT_SCHEMA_VERSION ||
    typeof value.requestId !== "string" ||
    !value.requestId ||
    (requestId !== undefined && value.requestId !== requestId) ||
    !isModelOutcome(value.outcome)
  ) {
    throw new TypeError("invalid Spirit Guide response value");
  }
  return value as SpiritGuideResponse;
}

export function parseTastingRoomResponse(value: unknown, requestId?: string): TastingRoomResponse {
  if (!isRecord(value) || !hasExactKeys(value, ["schemaVersion", "requestId", "answers", "fineTunedAnswer"])) {
    throw new TypeError("invalid Tasting Room response envelope");
  }
  if (!isRecord(value.answers) || !hasExactKeys(value.answers, ["1", "2"])) {
    throw new TypeError("invalid Tasting Room answers");
  }
  if (
    value.schemaVersion !== CHATGNT_SCHEMA_VERSION ||
    typeof value.requestId !== "string" ||
    !value.requestId ||
    (requestId !== undefined && value.requestId !== requestId) ||
    (value.fineTunedAnswer !== 1 && value.fineTunedAnswer !== 2) ||
    !isModelOutcome(value.answers[1]) ||
    !isModelOutcome(value.answers[2])
  ) {
    throw new TypeError("invalid Tasting Room response value");
  }
  return value as TastingRoomResponse;
}
