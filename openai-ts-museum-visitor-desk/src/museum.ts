import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export interface MuseumFacts {
  name: string;
  hours: string[];
  tickets: string[];
  exhibits: string[];
  accessibility: string[];
  escalation: string;
}

const FACTS_PATH = fileURLToPath(new URL("../data/museum.json", import.meta.url));

export function loadFacts(path: string = FACTS_PATH): MuseumFacts {
  return JSON.parse(readFileSync(path, "utf8")) as MuseumFacts;
}

const bullets = (items: string[]): string => items.map((i) => `- ${i}`).join("\n");

export function buildSystemPrompt(facts: MuseumFacts): string {
  return [
    `You are the visitor-desk assistant for ${facts.name}. Be warm, brief and concrete.`,
    "Answer only from the facts below. If something is not covered, say so and " +
      facts.escalation,
    "",
    "Opening hours:",
    bullets(facts.hours),
    "",
    "Tickets:",
    bullets(facts.tickets),
    "",
    "Current exhibits:",
    bullets(facts.exhibits),
    "",
    "Accessibility:",
    bullets(facts.accessibility),
  ].join("\n");
}
