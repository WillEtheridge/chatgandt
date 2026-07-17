import "server-only";

import type { ChatGntProvider } from "@/server/chatgnt-provider";

let provider: ChatGntProvider | undefined;

export async function getChatGntProvider(): Promise<ChatGntProvider> {
  if (provider) return provider;
  const { HuggingFaceChatGntProvider } = await import("@/server/huggingface-provider");
  provider = new HuggingFaceChatGntProvider();
  return provider;
}
