import tools


def test_lookup_known_and_unknown_policy():
    assert tools.lookup_policy("aut-20417")["holder"] == "Marisol Quenby"
    assert "error" in tools.lookup_policy("NOPE-1")


def test_coverage_applies_deductible_and_limit():
    assert tools.check_coverage("AUT-20417", "collision", 2300)["estimated_payout_usd"] == 1800
    assert tools.check_coverage("AUT-20417", "glass", 5000)["estimated_payout_usd"] == 1200


def test_uncovered_and_inactive_policies_are_refused():
    assert tools.check_coverage("AUT-20417", "flood", 100)["covered"] is False
    assert tools.check_coverage("AUT-31188", "collision", 100)["reason"] == "policy is not active"


def test_open_claim_only_when_covered():
    before = len(tools.OPEN_CLAIMS)
    claim = tools.open_claim("HOM-77310", "water_damage", 6400, "burst pipe")
    assert claim["claim_id"].startswith("CLM-") and len(tools.OPEN_CLAIMS) == before + 1
    assert "error" in tools.open_claim("HOM-77310", "earthquake", 6400, "shaking")
    assert len(tools.OPEN_CLAIMS) == before + 1
