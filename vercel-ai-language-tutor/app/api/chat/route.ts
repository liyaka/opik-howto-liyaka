import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, streamText, type UIMessage } from "ai";
import { findLesson } from "@/lib/lessons";
import { buildSystemPrompt } from "@/lib/persona";
import { tutorTelemetry } from "@/lib/telemetry";

export const maxDuration = 30;

export async function POST(req: Request) {
  const { id, lessonId, messages } = (await req.json()) as {
    id: string;
    lessonId?: string;
    messages: UIMessage[];
  };
  const lesson = findLesson(lessonId);

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: buildSystemPrompt(lesson),
    messages: await convertToModelMessages(messages),
    // id is the learner session; Opik turns it into the thread id so the turns
    // of one session read as one conversation in the Threads tab.
    runtimeContext: { threadId: id, lessonId: lesson.id, traceName: "tutor-turn" },
    experimental_telemetry: tutorTelemetry(),
  });

  return result.toUIMessageStreamResponse();
}
