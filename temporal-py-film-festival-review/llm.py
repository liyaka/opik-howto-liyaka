"""One small helper around the OpenAI client, used by the two LLM activities."""

import json
import os

from openai import AsyncOpenAI
from opentelemetry import trace

tracer = trace.get_tracer("festival-llm")

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


async def chat(system: str, user: str, *, json_mode: bool = False) -> str:
    client = AsyncOpenAI()
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    # Hand-made span with gen_ai.* attributes: Opik ingests it as an llm span, reading the model,
    # prompt/completion and token usage; gen_ai.system is what lets it price the call.
    with tracer.start_as_current_span(f"chat {MODEL}") as span:
        span.set_attribute("gen_ai.system", "openai")
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.request.model", MODEL)
        span.set_attribute("gen_ai.prompt", json.dumps(messages))
        response = await client.chat.completions.create(
            model=MODEL,
            temperature=0.2,
            messages=messages,
            response_format={"type": "json_object"} if json_mode else {"type": "text"},
        )
        text = response.choices[0].message.content or ""
        span.set_attribute("gen_ai.response.model", response.model)
        span.set_attribute("gen_ai.completion", text)
        if response.usage:
            span.set_attribute("gen_ai.usage.input_tokens", response.usage.prompt_tokens)
            span.set_attribute("gen_ai.usage.output_tokens", response.usage.completion_tokens)
        return text


def parse_classification(raw: str) -> dict:
    """Parse the classifier's JSON and clamp it into the shape the workflow expects."""
    data = json.loads(raw)
    score = int(data.get("fit_score", 0))
    return {
        "genre": str(data.get("genre", "unknown")).strip().lower(),
        "fit_score": max(1, min(10, score)),
        "rationale": str(data.get("rationale", "")).strip(),
    }
