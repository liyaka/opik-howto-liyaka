import { describe, expect, it } from "vitest";
import { formatCandidates, loadCatalog, searchCatalog, tokenize } from "../src/catalog.js";

const catalog = loadCatalog();

describe("catalog search", () => {
  it("drops filler words when tokenizing", () => {
    expect(tokenize("I want a cozy mystery near the sea")).toEqual([
      "cozy", "mystery", "near", "sea",
    ]);
  });

  it("ranks tag matches first", () => {
    const hits = searchCatalog("cozy mystery by the coast", catalog);
    expect(hits[0].title).toBe("Salt Road Almanac");
  });

  it("matches plural forms", () => {
    const hits = searchCatalog("robots", catalog);
    expect(hits.map((b) => b.title)).toContain("Quiet Machines");
  });

  it("returns nothing for an empty or unknown query", () => {
    expect(searchCatalog("the a of", catalog)).toEqual([]);
    expect(formatCandidates([])).toContain("no catalog matches");
  });

  it("lists page counts so the model can answer 'anything shorter?'", () => {
    const text = formatCandidates(searchCatalog("short dragons", catalog));
    expect(text).toMatch(/128 pages/);
  });
});
