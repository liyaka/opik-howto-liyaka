"""Offline corpus of fictional ranger notes with a tiny keyword search."""

import math
import pathlib
import re

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

STOPWORDS = frozenset(
    "the a an and or of to in for is are was were be been what how why when "
    "which who did does do with on by as at it its from that this these those "
    "any some during over per season reserve kestrel hollow".split()
)


def load_corpus(data_dir: pathlib.Path = DATA_DIR) -> list[dict]:
    """One entry per '##' section of every markdown file in data/."""
    entries = []
    for path in sorted(data_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        for section in sections:
            entries.append({"source": path.name, "text": f"{title.strip()}\n\n## {section.strip()}"})
    return entries


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOPWORDS


def search(query: str, corpus: list[dict], k: int = 3) -> list[dict]:
    """Rank sections by the IDF-weighted query terms they contain."""
    terms = tokens(query)
    docs = [tokens(e["text"]) for e in corpus]

    def idf(term: str) -> float:
        df = sum(1 for d in docs if term in d)
        return math.log(len(corpus) / df) if df else 0.0

    scored = [(sum(idf(t) for t in terms if t in d), e) for d, e in zip(docs, corpus)]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [e for score, e in scored[:k] if score > 0]
