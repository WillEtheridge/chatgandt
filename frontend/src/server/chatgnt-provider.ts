import type { ModelOutcome, TastingRoomResponse } from "@/lib/chatgnt-contract";

export interface ChatGntProvider {
  generateSpiritGuide(prompt: string, requestId: string): Promise<ModelOutcome>;
  generateTasting(
    prompt: string,
    requestId: string,
  ): Promise<Pick<TastingRoomResponse, "answers" | "fineTunedAnswer">>;
}

export class ProviderConfigurationError extends Error {}
export class ProviderTimeoutError extends Error {}
export class ProviderUnavailableError extends Error {}
