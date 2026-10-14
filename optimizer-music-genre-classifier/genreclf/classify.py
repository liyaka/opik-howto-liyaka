"""Run a chat prompt over the songs with the OpenAI client."""

from openai import OpenAI

from genreclf.config import MODEL
from genreclf.metric import genre_accuracy


def make_client() -> OpenAI:
    return OpenAI()


def fill(messages: list[dict], song: str) -> list[dict]:
    """Substitute {song} in every message."""
    return [
        {**m, "content": m["content"].replace("{song}", song)}
        for m in messages
    ]


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
