import { describe, expect, it } from "vitest";
import { parsePromptRequest, RequestContractError } from "@/server/api-route";

function request(body: string, contentType = "application/json") {
  return new Request("http://localhost/api/spirit-guide", {
    body,
    headers: { "content-type": contentType },
    method: "POST",
  });
}

describe("prompt request contract", () => {
  it("trims and returns one prompt", async () => {
    await expect(parsePromptRequest(request('{"prompt":"  Help me choose  "}'))).resolves.toBe("Help me choose");
  });

  it.each([
    ["wrong content type", request('{"prompt":"hello"}', "text/plain")],
    ["invalid JSON", request("not-json")],
    ["extra field", request('{"prompt":"hello","extra":true}')],
    ["empty prompt", request('{"prompt":"   "}')],
    ["oversized prompt", request(JSON.stringify({ prompt: "x".repeat(501) }))],
  ])("rejects %s", async (_label, input) => {
    await expect(parsePromptRequest(input)).rejects.toBeInstanceOf(RequestContractError);
  });
});
