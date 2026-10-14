import checks


def test_planted_faults_are_detected():
    df = checks.load_readings()
    assert checks.stuck_sensor(df) == {"RIDGE-02": 14.3}
    bad = checks.impossible_humidity(df)
    assert list(bad["station"]) == ["HARBOR-03"] and bad["humidity_pct"].iloc[0] == 187.0
    assert checks.coverage_gaps(df) == {"VALLEY-04": 40}


def test_clean_station_has_no_faults():
    df = checks.load_readings()
    clean = df[df["station"] == "COAST-01"]
    assert checks.stuck_sensor(clean) == {}
    assert checks.impossible_humidity(clean).empty
    assert checks.coverage_gaps(clean) == {}


def test_ground_truth_lines_match_the_planted_faults():
    lines = checks.ground_truth(checks.load_readings())
    assert lines == [
        "RIDGE-02 repeats 14.3 C for 72 consecutive hours",
        "HARBOR-03 at 2026-03-13 13:00 reads 187.0% humidity",
        "VALLEY-04 is missing 40 hourly rows",
    ]
