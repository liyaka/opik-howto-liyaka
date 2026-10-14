from types import SimpleNamespace

import pytest

from genreclf import classify, library, prompts
from genreclf.dataset import GENRES, load_songs
from genreclf.metric import genre_accuracy, normalize
from genreclf.report import format_curve, pinned_link, score_curve


class StubClient:
    """Stands in for the OpenAI client: always answers with `reply`."""

    def __init__(self, reply: str):
        self.seen: list[list[dict]] = []
        create = lambda **kw: (self.seen.append(kw["messages"]) or SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=reply))]
        ))
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def test_dataset_is_balanced_and_uses_a_safe_field_name():
    songs = load_songs()
    assert len(songs) == 36
    assert {s["genre"] for s in songs} == set(GENRES)
    assert all(set(s) == {"song", "genre"} for s in songs)  # "description" is reserved by Opik datasets
    assert all(sum(s["genre"] == g for s in songs) == 6 for g in GENRES)


def test_metric_is_exact_match_after_light_normalising():
    item = {"genre": "jazz"}
    assert genre_accuracy(item, " Jazz. ") == 1.0
    assert genre_accuracy(item, "The genre of the song is jazz.") == 0.0
    assert normalize('"Hip-Hop"') == "hip-hop"


def test_prompt_formatting_fills_the_song_placeholder():
    filled = classify.fill(prompts.baseline_messages(), "slow fiddle tune")
    assert filled[1]["content"] == "slow fiddle tune"
    assert "{song}" not in str(filled)


def test_traced_classify_runs_with_tracking_disabled():
    client = StubClient("Folk")
    assert classify.classify(client, prompts.baseline_messages(), "banjo and harmonica") == "Folk"
    assert client.seen[0][1]["content"] == "banjo and harmonica"


def test_evaluate_scores_a_stubbed_model():
    songs = load_songs()
    accuracy, rows = classify.evaluate(StubClient("jazz"), prompts.baseline_messages(), songs)
    assert accuracy == pytest.approx(1 / 6)
    assert len(rows) == len(songs)


def test_library_converts_to_mustache():
    converted = library.to_mustache(prompts.baseline_messages())
    assert converted[1]["content"] == "{{song}}"


def test_score_curve_flattens_rounds_and_formats_bars():
    history = [
        {"trials": [{"score": 0.25}]},
        {"trials": [{"score": 0.5}, {"score": None}, {"score": 0.75}]},
    ]
    points = score_curve(0.1, history)
    assert points == [(0, 0.1), (1, 0.25), (2, 0.5), (3, 0.75)]
    assert "best so far 0.750" in format_curve(points).splitlines()[-1]


def test_pinned_link_names_the_project():
    link = pinned_link("http://localhost:5173/", "default", "proj1", "opt1")
    assert link == "http://localhost:5173/default/projects/proj1/optimizations/opt1"
