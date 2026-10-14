"""Turn an optimizer history into a score curve and a project-pinned link."""

from typing import Any


def score_curve(initial: float, history: list[Any]) -> list[tuple[int, float]]:
    """[(0, baseline score), (1, first candidate), ...] in the order they were scored.

    The optimizer's history holds candidate trials only, so the baseline
    score is prepended. Rounds may be dicts or objects with a `.trials` list;
    trials without a score are skipped.
    """
    points: list[tuple[int, float]] = [(0, float(initial))]
    for round_ in history:
        trials = round_.get("trials") if isinstance(round_, dict) else round_.trials
        for trial in trials or []:
            score = trial.get("score") if isinstance(trial, dict) else getattr(trial, "score", None)
            if score is not None:
                points.append((len(points), float(score)))
    return points


def format_curve(points: list[tuple[int, float]], width: int = 30) -> str:
    """One bar per trial, so the climb is visible in a terminal."""
    lines = []
    best = 0.0
    for index, score in points:
        best = max(best, score)
        label = "baseline" if index == 0 else f"trial {index}"
        lines.append(f"  {label:<9} {score:.3f} {'#' * round(score * width):<{width}} best so far {best:.3f}")
    return "\n".join(lines)


def pinned_link(ui_base: str, workspace: str, project_id: str, optimization_id: str) -> str:
    """URL that opens the run inside its own project."""
    return f"{ui_base.rstrip('/')}/{workspace}/projects/{project_id}/optimizations/{optimization_id}"
