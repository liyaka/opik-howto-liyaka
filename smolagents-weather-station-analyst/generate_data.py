"""Regenerate data/readings.csv: four fictional weather stations, hourly, 21 days.

Three faults are planted on purpose so the agent has real findings to verify:
  - RIDGE-02  temperature sensor stuck at 14.3 C for 72 hours
  - HARBOR-03 one impossible humidity reading (187 %)
  - VALLEY-04 a 40-hour outage with no rows at all
"""

import math
import random
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).parent / "data" / "readings.csv"
START = datetime(2026, 3, 1)
HOURS = 21 * 24

# station -> (mean temp, daily swing, mean humidity, mean wind kph, mean pressure hPa)
STATIONS = {
    "COAST-01": (11.0, 4.0, 78, 22, 1013),
    "RIDGE-02": (7.0, 5.0, 65, 31, 968),
    "HARBOR-03": (12.5, 3.5, 82, 18, 1012),
    "VALLEY-04": (9.5, 8.0, 70, 9, 1005),
}


def build_rows() -> list[str]:
    rng = random.Random(2026)
    rows = ["station,timestamp,temp_c,humidity_pct,wind_kph,pressure_hpa,rain_mm"]
    for name, (temp, swing, hum, wind, pres) in STATIONS.items():
        for h in range(HOURS):
            ts = START + timedelta(hours=h)
            if name == "VALLEY-04" and 200 <= h < 240:
                continue  # sensor outage: the rows are simply absent
            t = temp + swing * math.sin((ts.hour - 9) / 24 * 2 * math.pi) + rng.gauss(0, 0.6)
            if name == "RIDGE-02" and 120 <= h < 192:
                t = 14.3  # stuck sensor
            rh = min(99.0, max(30.0, hum - 0.8 * (t - temp) + rng.gauss(0, 3)))
            if name == "HARBOR-03" and h == 301:
                rh = 187.0  # impossible reading
            ws = max(0.0, wind + rng.gauss(0, 5))
            p = pres + 6 * math.sin(h / 53) + rng.gauss(0, 0.8)
            rain = round(rng.expovariate(1.8), 1) if rng.random() < 0.12 else 0.0
            rows.append(
                f"{name},{ts:%Y-%m-%d %H:%M},{t:.1f},{rh:.1f},{ws:.1f},{p:.1f},{rain}"
            )
    return rows


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(build_rows()) + "\n")
    print(f"wrote {OUT}")
