"""Exact-match scoring: the model's whole answer has to be the genre."""


def normalize(answer: str) -> str:
    """Lowercase and strip quotes and punctuation, so "Jazz." passes."""
    return answer.strip().lower().strip(".!\"'` *")


def genre_accuracy(dataset_item: dict, llm_output: str) -> float:
    """1.0 if the answer is exactly the labelled genre, else 0.0.

    "This sounds like jazz" scores 0.0 on purpose: the output format is part
    of what a good prompt has to pin down.
    """
    return 1.0 if normalize(llm_output) == dataset_item["genre"] else 0.0
