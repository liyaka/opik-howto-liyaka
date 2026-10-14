import lessonData from "../data/lessons.json";

export interface VocabItem {
  es: string;
  en: string;
}

export interface Lesson {
  id: string;
  title: string;
  level: string;
  goal: string;
  vocab: VocabItem[];
  grammarFocus: string;
}

export const lessons: Lesson[] = lessonData;

export function findLesson(id: string | undefined): Lesson {
  const lesson = lessons.find((l) => l.id === id) ?? lessons[0];
  if (!lesson) throw new Error("data/lessons.json has no lessons");
  return lesson;
}

export function formatLesson(lesson: Lesson): string {
  const vocab = lesson.vocab.map((v) => `- ${v.es} = ${v.en}`).join("\n");
  return [
    `Lesson: ${lesson.title} (${lesson.level})`,
    `Goal: ${lesson.goal}`,
    `Grammar focus: ${lesson.grammarFocus}`,
    `Vocabulary:\n${vocab}`,
  ].join("\n");
}
