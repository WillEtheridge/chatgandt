import type { ChatGntRecipe } from "@/components/recipe";
import type { AnswerNumber, ModelOutcome } from "@/lib/chatgnt-contract";
import type { ChatGntProvider } from "@/server/chatgnt-provider";

const RECIPES: Record<AnswerNumber, ChatGntRecipe> = {
  1: {
    garnish: "One clear worktop as visible proof of progress.",
    ingredients: [
      { amount: 50, name: "functional impact", unit: "ml" },
      { amount: 25, name: "visible progress", unit: "ml" },
      { amount: 15, name: "uninterrupted focus", unit: "minutes" },
      { amount: 2, name: "hazard awareness", unit: "dashes" },
      { amount: 1, name: "basket for anything belonging elsewhere", unit: "measure" },
    ],
    method: [
      "Skim off anything urgent—spills, spoiled food, or blocked walkways—before choosing the main pour.",
      "Stir functional impact together with visible progress, then choose the chore that will restore the most useful space within fifteen minutes.",
      "Pour your full attention into that one task, straining anything that belongs elsewhere into the basket instead of leaving the room.",
      "Serve the finished win, then decide whether to stop or mix a second round.",
    ],
    title: "The Clear-Surface Collins",
  },
  2: {
    garnish: "A cleared patch of room and permission to stop after one useful win.",
    ingredients: [
      { amount: 45, name: "most useful room", unit: "ml" },
      { amount: 30, name: "quick visible win", unit: "ml" },
      { amount: 15, name: "focused effort", unit: "minutes" },
      { amount: 1, name: "temporary clutter basket", unit: "measure" },
    ],
    method: [
      "Choose the room whose mess is getting in the way of daily life most often.",
      "Pick one task that creates a visible result in fifteen minutes: clear a worktop, wash the dishes, or gather loose laundry.",
      "Put anything that belongs elsewhere into one basket so you can finish without wandering between rooms.",
      "Stop when the timer ends, notice the improvement, and only continue if you genuinely have the energy.",
    ],
    title: "The First-Win Highball",
  },
};

function outcome(recipe: ChatGntRecipe): ModelOutcome {
  return { status: "valid", recipe };
}

export class MockChatGntProvider implements ChatGntProvider {
  async generateSpiritGuide(): Promise<ModelOutcome> {
    return outcome(RECIPES[1]);
  }

  async generateTasting() {
    const fineTunedAnswer: AnswerNumber = crypto.getRandomValues(new Uint8Array(1))[0] % 2 === 0 ? 1 : 2;
    return {
      answers: {
        1: outcome(fineTunedAnswer === 1 ? RECIPES[1] : RECIPES[2]),
        2: outcome(fineTunedAnswer === 2 ? RECIPES[1] : RECIPES[2]),
      },
      fineTunedAnswer,
    };
  }
}
