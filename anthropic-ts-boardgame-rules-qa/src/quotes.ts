// Pure helpers: pull <quote> excerpts out of an answer and check them against the rulebook.

export function extractQuotes(answer: string): string[] {
  return [...answer.matchAll(/<quote>([\s\S]*?)<\/quote>/g)].map((m) => (m[1] ?? "").trim());
}

// A quote is faithful only if it appears character for character in the rulebook.
// Line wrapping in the source file is the one thing we forgive.
function squash(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

export interface QuoteCheck {
  quote: string;
  verbatim: boolean;
}

export function checkQuotes(answer: string, rulebook: string): QuoteCheck[] {
  const haystack = squash(rulebook);
  return extractQuotes(answer).map((quote) => ({
    quote,
    verbatim: quote.length > 0 && haystack.includes(squash(quote)),
  }));
}
