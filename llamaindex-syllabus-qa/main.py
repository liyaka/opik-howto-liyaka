"""Q&A over generated course-syllabus PDFs with LlamaIndex."""

import pathlib

import dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

import syllabi

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")
dotenv.load_dotenv()

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

SYSTEM_HINT = (
    "You answer questions about university course syllabi. Answer only from the retrieved "
    "syllabus excerpts, and name the course you are answering about. If the excerpts do not "
    "cover the question, say so."
)

DEMO_QUESTIONS = [
    "What is the late penalty for homework in CS 340?",
    "What are the grading weights in Marine Ecology?",
    "When and where are Prof. Lindgren's office hours?",
    "What are the prerequisites for the databases course?",
    "When is the BIO 210 final exam?",
]


def build_query_engine():
    if not sorted(syllabi.DATA_DIR.glob("*.pdf")):
        syllabi.generate_all()
    documents = SimpleDirectoryReader(str(syllabi.DATA_DIR)).load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index.as_query_engine(similarity_top_k=3)


def ask(query_engine, question: str):
    return query_engine.query(f"{SYSTEM_HINT}\n\nQuestion: {question}")


def main() -> None:
    query_engine = build_query_engine()
    for question in DEMO_QUESTIONS:
        print(f"Q: {question}\nA: {ask(query_engine, question)}\n")


if __name__ == "__main__":
    main()
