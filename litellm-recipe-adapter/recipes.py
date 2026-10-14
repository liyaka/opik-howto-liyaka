"""Recipe data, prompt building and the per-model summary. No Opik, no network."""

import json
import statistics
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).parent / "data"

MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-haiku-4-5-20251001",
]


@dataclass
class Call:
    model: str
    latency_s: float
    tokens: int
    cost_usd: float


def load_requests() -> list[dict]:
    """Join each adaptation request with the recipe it refers to."""
    recipes = {r["id"]: r for r in json.loads((DATA / "recipes.json").read_text())}
    requests = json.loads((DATA / "requests.json").read_text())
    return [{**req, "recipe_data": recipes[req["recipe"]]} for req in requests]


def build_prompt(request: dict) -> str:
    recipe = request["recipe_data"]
    ingredients = "\n".join(f"- {i}" for i in recipe["ingredients"])
    steps = "\n".join(f"{n}. {s}" for n, s in enumerate(recipe["steps"], 1))
    return (
        f"Recipe: {recipe['title']} (serves {recipe['servings']})\n"
        f"Ingredients:\n{ingredients}\nSteps:\n{steps}\n\n"
        f"Task: {request['instruction']}\n"
        "Return the adapted ingredient list and steps, then one line on what you changed."
    )


def summarize(calls: list[Call]) -> list[dict]:
    """One row per model: calls, mean latency, total tokens, total cost."""
    rows = []
    for model in dict.fromkeys(c.model for c in calls):
        mine = [c for c in calls if c.model == model]
        rows.append({
            "model": model,
            "calls": len(mine),
            "avg_latency_s": statistics.mean(c.latency_s for c in mine),
            "tokens": sum(c.tokens for c in mine),
            "cost_usd": sum(c.cost_usd for c in mine),
        })
    return rows


def format_table(rows: list[dict]) -> str:
    head = f"{'model':<38}{'calls':>6}{'avg latency':>13}{'tokens':>8}{'total cost':>13}"
    lines = [head, "-" * len(head)]
    for r in rows:
        lines.append(
            f"{r['model'].split('/')[-1]:<38}{r['calls']:>6}"
            f"{r['avg_latency_s']:>12.2f}s{r['tokens']:>8}{'$' + format(r['cost_usd'], '.6f'):>13}"
        )
    return "\n".join(lines)
