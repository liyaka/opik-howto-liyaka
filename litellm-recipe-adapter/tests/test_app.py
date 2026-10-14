import litellm
from types import SimpleNamespace

import main
from recipes import Call, build_prompt, format_table, load_requests, summarize


def test_requests_join_recipes():
    requests = load_requests()
    assert len(requests) == 6
    assert {r["kind"] for r in requests} == {"vegan", "gluten-free", "servings", "allergen-swap"}
    assert all(r["recipe_data"]["id"] == r["recipe"] for r in requests)


def test_prompt_contains_recipe_and_task():
    request = load_requests()[0]
    prompt = build_prompt(request)
    assert "Moonlit Lasagna" in prompt and "500 g ground beef" in prompt
    assert "fully vegan" in prompt


def test_summarize_totals_per_model():
    calls = [
        Call("a/x", 1.0, 100, 0.001),
        Call("a/x", 3.0, 50, 0.002),
        Call("b/y", 2.0, 10, 0.5),
    ]
    rows = summarize(calls)
    assert rows[0] == {"model": "a/x", "calls": 2, "avg_latency_s": 2.0, "tokens": 150, "cost_usd": 0.003}
    assert rows[1]["calls"] == 1
    assert "x" in format_table(rows)


def test_traced_function_runs_with_tracking_disabled(monkeypatch):
    # adapt_recipe is wrapped by @opik.track; with OPIK_TRACK_DISABLE it is a plain call, so the
    # model client can be stubbed and the function unit-tested.
    fake = SimpleNamespace(usage=SimpleNamespace(total_tokens=42), _hidden_params={"response_cost": 0.01})
    monkeypatch.setattr(litellm, "completion", lambda **kw: fake)
    call = main.adapt_recipe("openai/gpt-4o-mini", load_requests()[0])
    assert (call.tokens, call.cost_usd, call.model) == (42, 0.01, "openai/gpt-4o-mini")
