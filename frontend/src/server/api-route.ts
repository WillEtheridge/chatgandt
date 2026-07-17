import {
  CHATGNT_SCHEMA_VERSION,
  MAX_PROMPT_CHARACTERS,
  type ApiErrorCode,
  type ApiErrorResponse,
} from "@/lib/chatgnt-contract";
import {
  ProviderConfigurationError,
  ProviderTimeoutError,
  ProviderUnavailableError,
} from "@/server/chatgnt-provider";

const MAX_REQUEST_BYTES = 4096;
const JSON_HEADERS = { "cache-control": "no-store", "content-type": "application/json" };

export class RequestContractError extends Error {}

export function requestId(): string {
  return crypto.randomUUID();
}

export async function parsePromptRequest(request: Request): Promise<string> {
  const contentType = request.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase();
  if (contentType !== "application/json") throw new RequestContractError("Expected an application/json request.");
  const declaredLength = Number(request.headers.get("content-length"));
  if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
    throw new RequestContractError("Request body is too large.");
  }
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > MAX_REQUEST_BYTES) {
    throw new RequestContractError("Request body is too large.");
  }
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    throw new RequestContractError("Request body must be valid JSON.");
  }
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new RequestContractError("Request body must be an object containing one prompt.");
  }
  const record = value as Record<string, unknown>;
  if (Object.keys(record).length !== 1 || typeof record.prompt !== "string") {
    throw new RequestContractError("Request body must contain exactly one string field named prompt.");
  }
  const prompt = record.prompt.trim();
  if (!prompt) throw new RequestContractError("Prompt must not be empty.");
  if ([...prompt].length > MAX_PROMPT_CHARACTERS) {
    throw new RequestContractError(`Prompt must be ${MAX_PROMPT_CHARACTERS} characters or fewer.`);
  }
  return prompt;
}

export function originAllowed(request: Request): boolean {
  if (process.env.NODE_ENV !== "production") return true;
  const allowedOrigin = process.env.CHATGNT_ALLOWED_ORIGIN;
  return Boolean(allowedOrigin && request.headers.get("origin") === allowedOrigin);
}

export function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), { headers: JSON_HEADERS, status });
}

export function errorResponse(id: string, code: ApiErrorCode, message: string, status: number): Response {
  const body: ApiErrorResponse = {
    error: { code, message },
    requestId: id,
    schemaVersion: CHATGNT_SCHEMA_VERSION,
  };
  return jsonResponse(body, status);
}

export function providerErrorResponse(id: string, error: unknown): Response {
  if (error instanceof ProviderConfigurationError) {
    return errorResponse(id, "configuration_error", "The model service is not configured.", 500);
  }
  if (error instanceof ProviderTimeoutError) {
    return errorResponse(id, "provider_timeout", "The model service took too long to answer.", 504);
  }
  if (error instanceof ProviderUnavailableError) {
    return errorResponse(id, "provider_unavailable", "The model service could not complete this order.", 502);
  }
  return errorResponse(id, "provider_unavailable", "The model service could not complete this order.", 502);
}
