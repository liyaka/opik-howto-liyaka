import { readFileSync } from "node:fs";

export interface Episode {
  slug: string;
  summary: string;
}

export function loadEpisodes(): Episode[] {
  const path = new URL("../data/episodes.json", import.meta.url);
  return JSON.parse(readFileSync(path, "utf8")) as Episode[];
}
