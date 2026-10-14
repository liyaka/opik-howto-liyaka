import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export interface Book {
  id: string;
  title: string;
  author: string;
  genre: string;
  pages: number;
  tags: string[];
  blurb: string;
}

const here = path.dirname(fileURLToPath(import.meta.url));

export function loadCatalog(): Book[] {
  const file = path.join(here, "../data/catalog.json");
  return JSON.parse(readFileSync(file, "utf8")) as Book[];
}

const STOP = new Set([
  "a", "an", "the", "i", "me", "my", "and", "or", "of", "to", "for", "with",
  "in", "on", "is", "it", "that", "this", "any", "anything", "something",
  "like", "love", "want", "would", "please", "book", "books", "read", "can",
  "you", "have", "got", "some", "more", "what", "do", "does", "are", "be",
]);

export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z]+/)
    .filter((w) => w.length > 2 && !STOP.has(w));
}

function stem(word: string): string {
  return word.replace(/(ies|es|s|ing|ed)$/, "");
}

/** Rank books by keyword overlap with the query: tags and genre count double. */
export function searchCatalog(query: string, catalog: Book[], limit = 4): Book[] {
  const words = new Set(tokenize(query).map(stem));
  if (words.size === 0) return [];
  const scored = catalog.map((book) => {
    const strong = new Set(
      [...book.tags, book.genre].flatMap((t) => tokenize(t)).map(stem),
    );
    const weak = new Set(tokenize(`${book.title} ${book.blurb}`).map(stem));
    let score = 0;
    for (const w of words) {
      if (strong.has(w)) score += 2;
      else if (weak.has(w)) score += 1;
    }
    return { book, score };
  });
  return scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score || a.book.pages - b.book.pages)
    .slice(0, limit)
    .map((s) => s.book);
}

export function formatCandidates(docs: { pageContent: string }[]): string {
  if (docs.length === 0) return "(no catalog matches for this request)";
  return docs.map((d) => `- ${d.pageContent}`).join("\n");
}
