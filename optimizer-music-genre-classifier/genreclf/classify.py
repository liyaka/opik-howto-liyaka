"""Run a chat prompt over the songs with the OpenAI client."""

import opik
from openai import OpenAI
from opik.integrations.openai import track_openai

from genreclf.config import MODEL, PROJECT_NAME
from genreclf.metric import genre_accuracy


def make_client() -> OpenAI:
    # track_openai wraps the client: every completion becomes an llm span with
    # the messages, token usage and cost, filed under the project below.
    return track_openai(OpenAI(), project_name=PROJECT_NAME)


def fill(messages: list[dict], song: str) -> list[dict]:
    """Substitute {song} in every message."""
    return [
        {**m, "content": m["content"].replace("{song}", song)}
        for m in messages
    ]


# @opik.track opens one trace per song, so the llm span from track_openai nests
# under a "classify_song" root instead of arriving as 36 anonymous traces.
@opik.track(name="classify_song", project_name=PROJECT_NAME)
def classify(client: OpenAI, messages: list[dict], song: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=fill(messages, song),
        temperature=0,
    )
    return response.choices[0].message.content or ""


def evaluate(client: OpenAI, messages: list[dict], songs: list[dict]) -> tuple[float, list[dict]]:
    """Return (accuracy, per-song rows) for a prompt."""
    rows = []
    for song in songs:
        answer = classify(client, messages, song["song"])
        rows.append(
            {"genre": song["genre"], "answer": answer, "score": genre_accuracy(song, answer)}
        )
    return sum(r["score"] for r in rows) / len(rows), rows
