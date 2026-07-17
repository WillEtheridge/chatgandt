import { CHATGNT_SCHEMA_VERSION, type SpiritGuideResponse } from "@/lib/chatgnt-contract";
import {
  RequestContractError,
  errorResponse,
  jsonResponse,
  originAllowed,
  parsePromptRequest,
  providerErrorResponse,
  requestId,
} from "@/server/api-route";
import { getChatGntProvider } from "@/server/provider-factory";

export const maxDuration = 300;
export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  const id = requestId();
  if (!originAllowed(request)) return errorResponse(id, "invalid_request", "Request origin is not allowed.", 403);
  let prompt: string;
  try {
    prompt = await parsePromptRequest(request);
  } catch (error) {
    if (error instanceof RequestContractError) return errorResponse(id, "invalid_request", error.message, 400);
    return errorResponse(id, "invalid_request", "The request could not be read.", 400);
  }
  try {
    const provider = await getChatGntProvider();
    const body: SpiritGuideResponse = {
      outcome: await provider.generateSpiritGuide(prompt, id),
      requestId: id,
      schemaVersion: CHATGNT_SCHEMA_VERSION,
    };
    return jsonResponse(body);
  } catch (error) {
    return providerErrorResponse(id, error);
  }
}
