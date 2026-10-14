#!/usr/bin/env bash
# Posts four sample sign-ups to the webhook and prints the coordinator card for each.
set -euo pipefail
URL="${WEBHOOK_URL:-http://localhost:5678/webhook/volunteer-signup}"

post() {
  echo "-- $1"
  for _ in $(seq 1 15); do
    if reply=$(curl -sf -X POST "$URL" -H 'Content-Type: application/json' -d "$2"); then
      echo "$reply" | python3 -m json.tool; echo; return 0
    fi
    sleep 2
  done
  echo "no answer from $URL; did ./setup.sh finish?" >&2; exit 1
}

post "Priya, retired, wants to drive" '{"name":"Priya Raman","age":"67","availability":"Tuesday and Thursday mornings","interests":"delivery driver","notes":"Retired school bus driver, full driving licence, happy to take the van to the north route."}'
post "Owen, 15, wants the warehouse" '{"name":"Owen Fairley","age":"15","availability":"Saturdays","interests":"warehouse sorting","notes":"Need volunteer hours for school. Strong, used to help at my uncle'"'"'s farm."}'
post "Marisol, vague sign-up" '{"name":"Marisol Ortega","age":"","availability":"whenever","interests":"anything","notes":"Want to help out!"}'
post "Grant, selling software" '{"name":"Grant Pell","age":"40","availability":"n/a","interests":"partnership","notes":"Our inventory SaaS cuts food waste 30%. Can I book 20 minutes with your director to demo it?"}'
