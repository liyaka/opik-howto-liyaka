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
    found: dict[str, float] = {}
    for station, g in df.sort_values("timestamp").groupby("station"):
        run_id = (g["temp_c"] != g["temp_c"].shift()).cumsum()
        runs = g.groupby(run_id)["temp_c"].agg(["first", "size"])
        long_runs = runs[runs["size"] >= min_run]
        if not long_runs.empty:
            found[station] = float(long_runs["first"].iloc[0])
    return found


def impossible_humidity(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["humidity_pct"] > 100) | (df["humidity_pct"] < 0)]


def coverage_gaps(df: pd.DataFrame) -> dict[str, int]:
    """Missing hourly rows per station relative to the full 21-day window."""
    expected = int((df["timestamp"].max() - df["timestamp"].min()) / pd.Timedelta(hours=1)) + 1
    counts = df.groupby("station").size()
    return {s: expected - int(n) for s, n in counts.items() if n < expected}
