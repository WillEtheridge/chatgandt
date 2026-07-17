import "server-only";

import { Client } from "@gradio/client";
import {
  parseSpiritGuideResponse,
  parseTastingRoomResponse,
  type ModelOutcome,
} from "@/lib/chatgnt-contract";
import {
  ProviderConfigurationError,
  ProviderTimeoutError,
  ProviderUnavailableError,
  type ChatGntProvider,
} from "@/server/chatgnt-provider";

const REQUEST_TIMEOUT_MS = 240_000;
let clientPromise: Promise<Client> | undefined;

function configuration(): { spaceId: string; token: `hf_${string}` } {
  const spaceId = process.env.HF_SPACE_ID;
  const token = process.env.HF_TOKEN;
  if (!spaceId || !token?.startsWith("hf_")) {
    throw new ProviderConfigurationError("Hugging Face inference is not configured");
  }
  return { spaceId, token: token as `hf_${string}` };
}

async function connectedClient(): Promise<Client> {
  if (!clientPromise) {
    const { spaceId, token } = configuration();
    clientPromise = Client.connect(spaceId, { token }).catch((error: unknown) => {
      clientPromise = undefined;
      throw error;
    });
  }
  return clientPromise;
}

async function submitWithTimeout(
  submission: ReturnType<Client["submit"]>,
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<unknown> {
  let timeout: ReturnType<typeof setTimeout> | undefined;
  const timedOut = new Promise<never>((_, reject) => {
    timeout = setTimeout(() => {
      void submission.cancel();
      reject(new ProviderTimeoutError("Hugging Face inference timed out"));
    }, timeoutMs);
  });
  const completed = (async () => {
    let result: unknown;
    for await (const event of submission) {
      if (event.type === "data") result = event.data[0];
      if (event.type === "status" && event.stage === "error") {
        throw new ProviderUnavailableError("Hugging Face inference failed");
      }
    }
    if (result === undefined) throw new ProviderUnavailableError("Hugging Face returned no result");
    return result;
  })();
  try {
    return await Promise.race([completed, timedOut]);
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

async function call(endpoint: string, prompt: string, requestId: string): Promise<unknown> {
  try {
    const client = await connectedClient();
    return await submitWithTimeout(client.submit(endpoint, { prompt, request_id: requestId }, undefined, undefined, true));
  } catch (error) {
    if (
      error instanceof ProviderConfigurationError ||
      error instanceof ProviderTimeoutError ||
      error instanceof ProviderUnavailableError
    ) {
      throw error;
    }
    throw new ProviderUnavailableError("Hugging Face inference is unavailable", { cause: error });
  }
}

export class HuggingFaceChatGntProvider implements ChatGntProvider {
  async generateSpiritGuide(prompt: string, requestId: string): Promise<ModelOutcome> {
    return parseSpiritGuideResponse(await call("/spirit_guide", prompt, requestId), requestId).outcome;
  }

  async generateTasting(prompt: string, requestId: string) {
    const response = parseTastingRoomResponse(await call("/tasting_room", prompt, requestId), requestId);
    return { answers: response.answers, fineTunedAnswer: response.fineTunedAnswer };
  }
}
