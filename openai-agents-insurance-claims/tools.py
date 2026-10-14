"""Plain claims logic over a fictional policy book. No model calls, so it is easy to test."""

import json
import uuid
from pathlib import Path

POLICIES = json.loads((Path(__file__).parent / "data" / "policies.json").read_text())

OPEN_CLAIMS: list[dict] = []


def lookup_policy(policy_number: str) -> dict:
    policy = POLICIES.get(policy_number.strip().upper())
    if policy is None:
        return {"error": f"no policy {policy_number}"}
    return {"policy_number": policy_number.strip().upper(), "holder": policy["holder"],
            "kind": policy["kind"], "active": policy["active"],
            "coverages": sorted(policy["coverages"])}


def check_coverage(policy_number: str, incident_type: str, amount_usd: float) -> dict:
    policy = POLICIES.get(policy_number.strip().upper())
    if policy is None:
        return {"error": f"no policy {policy_number}"}
    if not policy["active"]:
        return {"covered": False, "reason": "policy is not active"}
    cover = policy["coverages"].get(incident_type)
    if cover is None:
        return {"covered": False, "reason": f"{incident_type} is not covered by this policy"}
    payout = min(max(amount_usd - cover["deductible"], 0), cover["limit"])
    return {"covered": True, "deductible": cover["deductible"], "limit": cover["limit"],
            "estimated_payout_usd": payout}


def open_claim(policy_number: str, incident_type: str, amount_usd: float, summary: str) -> dict:
    verdict = check_coverage(policy_number, incident_type, amount_usd)
    if not verdict.get("covered"):
        return {"error": "claim not opened", "reason": verdict.get("reason", "not covered")}
    claim = {"claim_id": f"CLM-{uuid.uuid4().hex[:6].upper()}",
             "policy_number": policy_number.strip().upper(), "incident_type": incident_type,
             "amount_usd": amount_usd, "summary": summary, "status": "open"}
    OPEN_CLAIMS.append(claim)
    return claim
