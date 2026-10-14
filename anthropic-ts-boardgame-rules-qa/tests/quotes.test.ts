import { describe, expect, it } from "vitest";
import { RULEBOOK } from "../src/qa.js";
import { checkQuotes, extractQuotes } from "../src/quotes.js";

describe("quotes", () => {
  it("extracts every quoted excerpt", () => {
    const answer = "Yes. <quote>one</quote> and also <quote> two\nlines </quote>";
    expect(extractQuotes(answer)).toEqual(["one", "two\nlines"]);
  });

  it("accepts a quote copied from the rulebook, even across a line wrap", () => {
    const answer = "<quote>Wick tokens and lanterns in your stall do not count toward the hand limit.</quote>";
    expect(checkQuotes(answer, RULEBOOK)).toEqual([
      { quote: "Wick tokens and lanterns in your stall do not count toward the hand limit.", verbatim: true },
    ]);
  });

  it("flags a paraphrased quote", () => {
    const answer = "<quote>You can hold eight cards at most.</quote>";
    expect(checkQuotes(answer, RULEBOOK)[0]?.verbatim).toBe(false);
  });
});
