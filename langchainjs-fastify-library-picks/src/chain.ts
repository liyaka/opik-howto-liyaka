import {
  ChatPromptTemplate,
  MessagesPlaceholder,
} from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda, RunnableSequence } from "@langchain/core/runnables";
import type { RunnableConfig } from "@langchain/core/runnables";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";
import type { BaseMessage } from "@langchain/core/messages";
import { BaseRetriever } from "@langchain/core/retrievers";
import { Document } from "@langchain/core/documents";
import type { OpikCallbackHandler } from "opik-langchain";
import { formatCandidates, searchCatalog } from "./catalog.js";
import type { Book } from "./catalog.js";

export const SYSTEM_PROMPT = `You are the book-picking assistant for Elmwood Public Library.
Chat with the reader, learn what they enjoy, and recommend books ONLY from the
"Catalog matches" listed below. Name the title and author, give one sentence on
why it fits, and mention the page count when the reader cares about length.
If nothing in the matches fits, say so and ask one clarifying question.
Keep replies under 80 words; this is a small chat widget.`;

export interface Session {
  history: BaseMessage[];
  readerMessages: string[];
  opikHandler?: OpikCallbackHandler;
}

// A real LangChain retriever, not a plain lambda: opik-langchain reports retriever
// runs as `tool` spans with the matched documents as output, so catalog lookups
// are filterable by type and readable in the trace. A RunnableLambda shows up as a
// generic `general` span with a bare string output.
export class CatalogRetriever extends BaseRetriever {
  lc_namespace = ["library-picks", "catalog"];

  constructor(private readonly catalog: Book[]) {
    super();
  }

  async _getRelevantDocuments(query: string): Promise<Document[]> {
    return searchCatalog(query, this.catalog).map(
      (book) =>
        new Document({
          pageContent: `${book.title} by ${book.author} (${book.genre}, ${book.pages} pages): ${book.blurb}`,
          metadata: { id: book.id, pages: book.pages },
        }),
    );
  }
}

export function createChain(
  llm: BaseChatModel,
  sessions: Map<string, Session>,
  catalog: Book[],
) {
  const loadSession = RunnableLambda.from(
    (message: string, config?: RunnableConfig) => {
      const sessionId = (config?.configurable as { sessionId?: string })
        ?.sessionId;
      const session = sessionId ? sessions.get(sessionId) : undefined;
      if (!session) throw new Error(`Unknown session: ${sessionId}`);
      return {
        history: session.history,
        message,
        query: [...session.readerMessages, message].join(" "),
      };
    },
  ).withConfig({ runName: "load-session-history" });

  const retriever = new CatalogRetriever(catalog).withConfig({
    runName: "search-catalog",
  });
  // Passing `config` on is what nests the retriever run under this turn's trace.
  const retrieve = RunnableLambda.from(
    async (
      input: { history: BaseMessage[]; message: string; query: string },
      config?: RunnableConfig,
    ) => {
      const docs = await retriever.invoke(input.query, config);
      return {
        history: input.history,
        message: input.message,
        candidates: formatCandidates(docs),
      };
    },
  ).withConfig({ runName: "pick-candidates" });

  const prompt = ChatPromptTemplate.fromMessages([
    ["system", `${SYSTEM_PROMPT}\n\nCatalog matches:\n{candidates}`],
    new MessagesPlaceholder("history"),
    ["human", "{message}"],
  ]);

  return RunnableSequence.from([
    loadSession,
    retrieve,
    prompt,
    llm,
    new StringOutputParser(),
  ]);
}
