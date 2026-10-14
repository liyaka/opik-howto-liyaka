"""Route the same recipe-adaptation requests to two models through LiteLLM, traced by Opik."""

import logging
import os
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")
# The Opik project is read when the SDK client and LiteLLM's callback are created, so set it first.
os.environ["OPIK_PROJECT_NAME"] = "litellm-recipe-adapter"

import litellm
import opik
from litellm.integrations.opik.opik import OpikLogger
from opik import opik_context

from recipes import MODELS, Call, build_prompt, format_table, load_requests, summarize

# OpikLogger turns every litellm.completion into an llm span carrying usage and estimated cost.
# Outside an event loop it logs a harmless "no running event loop" error while creating itself; hide it.
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message=".*periodic_flush.*", category=RuntimeWarning)
litellm.callbacks = [OpikLogger()]
logging.getLogger("LiteLLM").setLevel(logging.WARNING)


# @track opens a trace per request (general span) that the LiteLLM llm span nests under;
# the model name in metadata and tags is what lets you group the traces table per model.
@opik.track(name="adapt_recipe")
def adapt_recipe(model: str, request: dict) -> Call:
    short = model.split("/")[-1]
    opik_context.update_current_trace(
        tags=[short, request["kind"]], metadata={"model": model, "recipe": request["recipe"]}
    )
    start = time.perf_counter()
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": build_prompt(request)}],
        # Without current_span_data the llm span is not attached to this trace and shows up as
        # a separate orphan trace; passing it nests the span under adapt_recipe.
        metadata={"opik": {"current_span_data": opik_context.get_current_span_data(), "tags": [short]}},
    )
    latency = time.perf_counter() - start
    return Call(
        model=model,
        latency_s=latency,
        tokens=response.usage.total_tokens,
        cost_usd=response._hidden_params.get("response_cost") or 0.0,
    )


def main() -> None:
    requests = load_requests()
    calls: list[Call] = []
    for model in MODELS:
        print(f"\n=== {model} ===")
        for request in requests:
            call = adapt_recipe(model, request)
            calls.append(call)
            print(f"  {request['recipe']:<18}{request['kind']:<14}"
                  f"{call.latency_s:5.2f}s {call.tokens:5d} tok ${call.cost_usd:.6f}")
    print("\n" + format_table(summarize(calls)))
    # flush_tracker sends the queued traces and spans before the process exits; without it the last ones can be lost.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
