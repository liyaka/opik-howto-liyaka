"""One small helper around the OpenAI client, used by the two LLM activities."""

import json
import os

from openai import AsyncOpenAI

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


async def chat(system: str, user: str, *, json_mode: bool = False) -> str:
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"} if json_mode else {"type": "text"},
    )
    return response.choices[0].message.content or ""


def parse_classification(raw: str) -> dict:
    """Parse the classifier's JSON and clamp it into the shape the workflow expects."""
    data = json.loads(raw)
    score = int(data.get("fit_score", 0))
    return {
        "genre": str(data.get("genre", "unknown")).strip().lower(),
        "fit_score": max(1, min(10, score)),
        "rationale": str(data.get("rationale", "")).strip(),
    }
