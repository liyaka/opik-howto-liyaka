import { describe, expect, it } from "vitest";
import { findLesson, formatLesson, lessons } from "../lib/lessons";
import { buildSystemPrompt, TUTOR_NAME } from "../lib/persona";

describe("lessons", () => {
  it("falls back to the first lesson for an unknown id", () => {
    expect(findLesson("nope").id).toBe(lessons[0]!.id);
  });

  it("lists every vocabulary item in the formatted lesson", () => {
    const lesson = findLesson("cafe-ordering");
    const text = formatLesson(lesson);
    for (const v of lesson.vocab) expect(text).toContain(`${v.es} = ${v.en}`);
  });
});

describe("persona", () => {
  it("builds a system prompt with the tutor name, lesson and rules", () => {
    const prompt = buildSystemPrompt(findLesson("weekend-plans"));
    expect(prompt).toContain(TUTOR_NAME);
    expect(prompt).toContain("fui");
    expect(prompt).toContain("exactly three");
  });
});
