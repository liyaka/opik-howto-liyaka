"""Local RAG over the beekeeping handbook: Ollama for chat and embeddings, in-memory vector store."""

import os
import pathlib

import opik
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import ChatOllama, OllamaEmbeddings

HERE = pathlib.Path(__file__).parent
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = "llama3.2:1b"
EMBED_MODEL = "nomic-embed-text"

SYSTEM_PROMPT = (
    "You are the Larkspur Hollow apiary assistant. Answer using only the handbook "
    "excerpts below. If they do not cover the question, say the handbook does not "
    "cover it. Answer in at most three sentences.\n\n{context}"
)


def load_chunks(docs_dir: pathlib.Path = HERE / "docs") -> list[str]:
    """One chunk per '##' section, prefixed with the document title."""
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        chunks += [f"{title.strip()}\n\n## {section.strip()}" for section in sections]
    return chunks


def format_context(texts: list[str]) -> str:
    return "\n\n---\n\n".join(texts)


def build_search(embeddings=None, k: int = 2):
    """Index the handbook and return a traced function: question -> top-k sections as one string."""
    embeddings = embeddings or OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_URL)
    store = InMemoryVectorStore.from_texts(load_chunks(), embeddings)
    retriever = store.as_retriever(search_kwargs={"k": k})

    # type="tool" makes this its own span carrying the question and the fetched sections;
    # a bare retriever in the chain does not show up in the trace.
    @opik.track(name="search_handbook", type="tool")
    def search_handbook(question: str) -> str:
        return format_context([d.page_content for d in retriever.invoke(question)])

    return search_handbook


def build_chain(embeddings=None, llm=None, k: int = 2):
    """Retrieve-then-answer chain over the handbook."""
    llm = llm or ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_URL, temperature=0, num_predict=200)
    search_handbook = build_search(embeddings, k)

    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", "{question}")])
    chain = (
        {"context": search_handbook, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    # run_name becomes the trace name in Opik
    return chain.with_config({"run_name": "ask_the_handbook"})
