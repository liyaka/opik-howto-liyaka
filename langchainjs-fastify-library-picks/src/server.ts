import path from "node:path";
import { fileURLToPath } from "node:url";

import dotenv from "dotenv";
import Fastify from "fastify";
import type { FastifyInstance } from "fastify";
import { ChatOpenAI } from "@langchain/openai";
import { AIMessage, HumanMessage } from "@langchain/core/messages";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

import { createChain } from "./chain.js";
import type { Session } from "./chain.js";
import { loadCatalog } from "./catalog.js";
import { Opik } from "opik";
import { OpikCallbackHandler } from "opik-langchain";

const here = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(here, "../.env"), quiet: true });
dotenv.config({ path: path.join(here, "../../.env"), quiet: true });

export const PROJECT_NAME = "langchainjs-fastify-library-picks";

// One shared client: every reader's traces batch through it, and flush() on it
// is what guarantees the last turns reach Opik before the process exits.
export const opikClient = new Opik({ projectName: PROJECT_NAME });

export async function flushOpik(): Promise<void> {
  await opikClient.flush();
}

interface ChatBody {
  message?: unknown;
  sessionId?: unknown;
}

export function buildApp(llm?: BaseChatModel): FastifyInstance {
  const model = llm ?? new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0.2 });
  const sessions = new Map<string, Session>();
  const chain = createChain(model, sessions, loadCatalog());
  const app = Fastify();

  app.post<{ Body: ChatBody }>("/chat", async (request, reply) => {
    const { message, sessionId } = request.body ?? {};
    if (
      typeof message !== "string" || !message.trim() ||
      typeof sessionId !== "string" || !sessionId
    ) {
      return reply
        .code(400)
        .send({ error: "Body must be { message: string, sessionId: string }" });
    }
    let session = sessions.get(sessionId);
    if (!session) {
      session = {
        history: [],
        readerMessages: [],
        // threadId = sessionId groups this reader's turns into one Opik thread.
        opikHandler: new OpikCallbackHandler({
          client: opikClient,
          threadId: sessionId,
        }),
      };
      sessions.set(sessionId, session);
    }
    try {
      const answer = await chain.invoke(message, {
        // The handler turns the chain run into a trace (root run) with child spans.
        callbacks: session.opikHandler ? [session.opikHandler] : [],
        runName: "library-picks-turn",
        configurable: { sessionId },
      });
      session.history.push(new HumanMessage(message), new AIMessage(answer));
      session.readerMessages.push(message);
      return { reply: answer, sessionId };
    } catch (error) {
      request.log.error(error);
      return reply.code(500).send({ error: "The picker could not answer." });
    }
  });

  return app;
}

const isMain =
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMain) {
  const port = Number(process.env.PORT ?? 3161);
  const app = buildApp();
  await app.listen({ port });
  for (const signal of ["SIGINT", "SIGTERM"] as const) {
    process.on(signal, async () => {
      await flushOpik();
      process.exit(0);
    });
  }
  console.log(`Library picks chat: POST http://localhost:${port}/chat`);
}
