from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import FakeListChatModel

import rag

TOPICS = ["swarm", "varroa", "honey", "winter", "inspect"]


class KeywordEmbeddings(Embeddings):
    """Offline stand-in: one dimension per topic word, so retrieval is deterministic."""

    def embed_documents(self, texts):
        return [[float(t.lower().count(w)) + 0.01 for w in TOPICS] for t in texts]

    def embed_query(self, text):
        return self.embed_documents([text])[0]


def test_chunks_are_one_per_section_with_title():
    chunks = rag.load_chunks()
    assert len(chunks) >= 15
    assert all("Larkspur Hollow Apiary Handbook" in c and "\n\n## " in c for c in chunks)


def test_format_context_separates_sections():
    assert rag.format_context(["a", "b"]) == "a\n\n---\n\nb"


def test_chain_retrieves_matching_section_and_answers():
    llm = FakeListChatModel(responses=["Every seven days."])
    chain = rag.build_chain(embeddings=KeywordEmbeddings(), llm=llm, k=1)
    assert chain.invoke("swarm swarm swarm season?") == "Every seven days."


def test_traced_search_runs_with_tracking_disabled():
    # @opik.track must not get in the way of plain calls when tracking is off.
    search = rag.build_search(embeddings=KeywordEmbeddings(), k=1)
    assert "Varroa Treatment Calendar" in search("varroa varroa mites")
