"""Run the Opik Agent Optimizer over the songs and keep the winner."""

import opik
from opik_optimizer import ChatPrompt, MetaPromptOptimizer

from genreclf import library
from genreclf.config import DATASET_NAME, MAX_TRIALS, MODEL, PROJECT_NAME
from genreclf.dataset import load_songs
from genreclf.metric import genre_accuracy
from genreclf.prompts import baseline_messages
from genreclf.report import format_curve, pinned_link, score_curve

# LiteLLM naming, used by the optimizer for both the task and its reasoning
OPTIMIZER_MODEL = f"openai/{MODEL}"


def ensure_dataset(client: opik.Opik) -> opik.Dataset:
    # An Opik dataset is the ground truth the optimizer scores every candidate
    # against. Identical rows are deduplicated, so re-runs reuse it.
    dataset = client.get_or_create_dataset(
        name=DATASET_NAME,
        description="36 fictional song descriptions labelled with one of six genres",
        project_name=PROJECT_NAME,
    )
    dataset.insert(load_songs())
    return dataset


def run(client: opik.Opik) -> None:
    dataset = ensure_dataset(client)
    library.save_baseline(client)

    messages = baseline_messages()
    prompt = ChatPrompt(
        name=PROJECT_NAME,
        system=messages[0]["content"],
        user=messages[1]["content"],
        model=OPTIMIZER_MODEL,
    )

    optimizer = MetaPromptOptimizer(
        model=OPTIMIZER_MODEL,  # reasons about why the prompt fails and drafts candidates
        prompts_per_round=3,
        seed=42,
        verbose=1,
    )
    # Each candidate is scored on every song and logged as an experiment under
    # one optimization run: that is the score curve in the Optimization runs
    # tab. project_name files the optimizer's own traces in this project.
    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=dataset,
        metric=genre_accuracy,
        n_samples=len(load_songs()),
        max_trials=MAX_TRIALS,
        project_name=PROJECT_NAME,
    )

    initial = result.initial_score if result.initial_score is not None else 0.0
    best = result.score

    print("\nScore curve across trials")
    print(format_curve(score_curve(initial, result.history)))
    print(f"\nbaseline accuracy : {initial:.3f}")
    print(f"best accuracy     : {best:.3f}  ({best - initial:+.3f})")
    print(f"trials completed  : {result.details.get('trials_completed')}  (budget: {MAX_TRIALS})")
    print(f"llm calls         : {result.llm_calls}")
    print(f"optimization run  : {run_link(client, result.optimization_id)}")

    if best > initial:
        winner = library.save_winner(
            client,
            result.prompt.get_messages(),
            f"MetaPromptOptimizer winner: accuracy {initial:.3f} -> {best:.3f} on {DATASET_NAME}",
            {
                "source": "MetaPromptOptimizer",
                "baseline_accuracy": round(initial, 3),
                "accuracy": round(best, 3),
                "dataset": DATASET_NAME,
            },
        )
        print(f"\nSaved the winner to the prompt library ({winner.commit}).")
    else:
        print("\nNo improvement over the baseline; the library keeps only version 1.")


def run_link(client: opik.Opik, optimization_id: str) -> str:
    # result.get_run_link() opens in whichever project the UI last showed, so
    # the run can look empty. This link names the optimization's own project.
    info = client.rest_client.optimizations.get_optimization_by_id(optimization_id)
    ui_base = client.config.url_override.rstrip("/").removesuffix("/api")
    return pinned_link(ui_base, client.config.workspace, info.project_id, optimization_id)
