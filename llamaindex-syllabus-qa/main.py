"""Q&A over generated course-syllabus PDFs with LlamaIndex."""

import pathlib

import dotenv
import opik
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.callbacks import CallbackManager
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from opik.integrations.llama_index import LlamaIndexCallbackHandler

import suite
import syllabi

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")
dotenv.load_dotenv()

PROJECT_NAME = "llamaindex-syllabus-qa"

# Registering the handler on Settings makes every query a trace: a retrieve span (with its
# embedding call) and a synthesize span ending in an llm span with token usage and cost.
# Without it nothing reaches Opik; project_name sends the traces to this project, not "Default Project".
Settings.callback_manager = CallbackManager([LlamaIndexCallbackHandler(project_name=PROJECT_NAME)])

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

    # Traces are sent from a background thread; flush so a short script does not exit before they upload.
    # Suite section: judge every question's assertions and record an experiment.
    suite.print_result(suite.run_suite(query_engine, ask, PROJECT_NAME))

    opik.flush_tracker()


if __name__ == "__main__":
    main()
