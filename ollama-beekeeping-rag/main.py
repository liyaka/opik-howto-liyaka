"""Ask a fully local RAG assistant three beekeeping questions and trace each with Opik."""

import os
import sys

PROJECT_NAME = "ollama-beekeeping-rag"
# Set before importing opik so @opik.track functions and the tracer share one project.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import dotenv
import opik
import requests
from opik.integrations.langchain import OpikTracer

dotenv.load_dotenv()

import rag  # noqa: E402  (after load_dotenv so OLLAMA_URL is honoured)

QUESTIONS = [
    "How often should I inspect hives during swarm season?",
    "When do I apply the late-summer varroa treatment, and with what if it is hot?",
    "How much honey must I leave the colony for winter?",
]


def check_ollama() -> None:
    try:
        tags = requests.get(f"{rag.OLLAMA_URL}/api/tags", timeout=3).json()
    except requests.RequestException:
        sys.exit(f"Ollama is not reachable at {rag.OLLAMA_URL}. Start it with `ollama serve`.")
    have = {m["name"] for m in tags["models"]}
    for model in (rag.CHAT_MODEL, rag.EMBED_MODEL):
        if model not in have and f"{model}:latest" not in have:
            sys.exit(f"Missing model: run `ollama pull {model}`")


def main() -> None:
    check_ollama()
    chain = rag.build_chain()
    # OpikTracer turns each chain run into one trace with an llm span for ChatOllama;
    # the tracked search_handbook span nests inside it.
    tracer = OpikTracer(project_name=PROJECT_NAME, tags=["ollama", "rag", "local"])
    for question in QUESTIONS:
        answer = chain.invoke(question, config={"callbacks": [tracer]})
        print(f"Q: {question}\nA: {answer}\n")
    # Traces are sent in the background; flush so none are lost when the script exits.
    tracer.flush()
    opik.flush_tracker()
    print(f"Done. Open the '{PROJECT_NAME}' project in Opik.")


if __name__ == "__main__":
    main()
