import "server-only";

import type { ChatGntProvider } from "@/server/chatgnt-provider";
import { ProviderConfigurationError } from "@/server/chatgnt-provider";

let provider: ChatGntProvider | undefined;

export async function getChatGntProvider(): Promise<ChatGntProvider> {
  if (provider) return provider;
  const backend = process.env.CHATGNT_BACKEND ?? (process.env.NODE_ENV === "production" ? undefined : "mock");
  if (backend === "mock") {
    const { MockChatGntProvider } = await import("@/server/mock-provider");
    provider = new MockChatGntProvider();
    return provider;
  }
  if (backend === "huggingface") {
    const { HuggingFaceChatGntProvider } = await import("@/server/huggingface-provider");
    provider = new HuggingFaceChatGntProvider();
    return provider;
  }
  throw new ProviderConfigurationError("CHATGNT_BACKEND must be mock or huggingface");
}
