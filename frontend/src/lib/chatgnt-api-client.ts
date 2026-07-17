import {
  CHATGNT_SCHEMA_VERSION,
  parseSpiritGuideResponse,
  parseTastingRoomResponse,
  type ApiErrorResponse,
  type SpiritGuideResponse,
  type TastingRoomResponse,
} from "@/lib/chatgnt-contract";

export class ChatGntApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: ApiErrorResponse["error"]["code"],
    message: string,
  ) {
    super(message);
    this.name = "ChatGntApiError";
  }
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (record.schemaVersion !== CHATGNT_SCHEMA_VERSION || typeof record.error !== "object" || record.error === null) return false;
  const error = record.error as Record<string, unknown>;
  return typeof error.code === "string" && typeof error.message === "string";
}

async function postPrompt(path: string, prompt: string): Promise<unknown> {
  const response = await fetch(path, {
    body: JSON.stringify({ prompt }),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ChatGntApiError(response.status, "provider_unavailable", "The model service returned an unreadable response.");
  }
  if (!response.ok) {
    if (isApiErrorResponse(body)) throw new ChatGntApiError(response.status, body.error.code, body.error.message);
    throw new ChatGntApiError(response.status, "provider_unavailable", "The model service could not complete this order.");
  }
  return body;
}

export async function requestSpiritGuide(prompt: string): Promise<SpiritGuideResponse> {
  return parseSpiritGuideResponse(await postPrompt("/api/spirit-guide", prompt));
}

export async function requestTastingRoom(prompt: string): Promise<TastingRoomResponse> {
  return parseTastingRoomResponse(await postPrompt("/api/tasting-room", prompt));
}
