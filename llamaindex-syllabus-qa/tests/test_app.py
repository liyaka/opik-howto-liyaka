import pytest
from llama_index.core import Settings
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

import main
import suite
import syllabi


@pytest.fixture
def mock_models(monkeypatch):
    monkeypatch.setattr(Settings, "llm", MockLLM(max_tokens=20))
    monkeypatch.setattr(Settings, "embed_model", MockEmbedding(embed_dim=8))


def test_generate_all_writes_three_readable_pdfs(tmp_path):
    from pypdf import PdfReader

    paths = syllabi.generate_all(tmp_path)
    assert len(paths) == 3
    text = " ".join(page.extract_text() for p in paths for page in PdfReader(p).pages)
    assert "10% of their score for each day" in text
    assert "48-hour grace token" in text


def test_committed_fixtures_match_the_generator(tmp_path):
    from pypdf import PdfReader

    for path in syllabi.generate_all(tmp_path):
        fresh = " ".join(pg.extract_text() for pg in PdfReader(path).pages)
        committed = " ".join(pg.extract_text() for pg in PdfReader(syllabi.DATA_DIR / path.name).pages)
        assert fresh == committed


def test_suite_items_are_well_formed():
    assert len(suite.SUITE_ITEMS) >= 6
    for item in suite.SUITE_ITEMS:
        assert item["question"].endswith("?")
        assert item["assertions"] and all(a.startswith("The answer") for a in item["assertions"])


def test_retrieval_returns_source_nodes_from_the_pdfs(mock_models):
    engine = main.build_query_engine()
    response = main.ask(engine, "Where are Prof. Lindgren's office hours?")
    assert 1 <= len(response.source_nodes) <= 3
    assert all(node.text for node in response.source_nodes)


def test_track_decorated_function_runs_with_tracking_disabled(mock_models):
    import opik

    @opik.track(name="syllabus_question")
    def traced(question):
        return str(main.ask(main.build_query_engine(), question))

    assert traced("What is the late policy?")
