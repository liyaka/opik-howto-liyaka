"""Ground truth for the planted faults, computed directly with pandas.

The agent's answers are compared against these, so a plausible-looking but
wrongly computed answer is caught instead of trusted.
"""

from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).parent / "data" / "readings.csv"


def load_readings(path: Path = CSV_PATH) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["timestamp"])


def stuck_sensor(df: pd.DataFrame, min_run: int = 24) -> dict[str, float]:
    """Stations whose temp_c repeats the exact same value for min_run+ hours in a row."""
    return {s: v for s, (v, _) in stuck_runs(df, min_run).items()}


def stuck_runs(df: pd.DataFrame, min_run: int = 24) -> dict[str, tuple[float, int]]:
    """Like stuck_sensor, but also returns the run length in hours."""
    found: dict[str, tuple[float, int]] = {}
    for station, g in df.sort_values("timestamp").groupby("station"):
        run_id = (g["temp_c"] != g["temp_c"].shift()).cumsum()
        runs = g.groupby(run_id)["temp_c"].agg(["first", "size"])
        long_runs = runs[runs["size"] >= min_run]
        if not long_runs.empty:
            found[station] = (float(long_runs["first"].iloc[0]), int(long_runs["size"].iloc[0]))
    return found


def impossible_humidity(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["humidity_pct"] > 100) | (df["humidity_pct"] < 0)]


def coverage_gaps(df: pd.DataFrame) -> dict[str, int]:
    """Missing hourly rows per station relative to the full 21-day window."""
    expected = int((df["timestamp"].max() - df["timestamp"].min()) / pd.Timedelta(hours=1)) + 1
    counts = df.groupby("station").size()
    return {s: expected - int(n) for s, n in counts.items() if n < expected}


def ground_truth(df: pd.DataFrame) -> list[str]:
    """One expected-answer line per question in agent.QUESTIONS."""
    (station, (value, hours)), = stuck_runs(df).items()
    bad = impossible_humidity(df).iloc[0]
    (gap_station, missing), = coverage_gaps(df).items()
    return [
        f"{station} repeats {value} C for {hours} consecutive hours",
        f"{bad['station']} at {bad['timestamp']:%Y-%m-%d %H:%M} reads {bad['humidity_pct']}% humidity",
        f"{gap_station} is missing {missing} hourly rows",
    ]
