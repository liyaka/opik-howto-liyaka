#!/usr/bin/env bash
# Starts n8n, claims the instance, stores the OpenAI credential and imports + activates
# the volunteer-screening workflow. Headless: no browser step.
set -euo pipefail
cd "$(dirname "$0")"

BASE="http://localhost:5678"
OWNER_EMAIL="coordinator@example.org"
OWNER_PASSWORD="Riverbend-demo-1"
BROWSER_ID="riverbend-setup"

ROOT_ENV="$(git rev-parse --show-toplevel 2>/dev/null || echo ..)/.env"
if [ -f "$ROOT_ENV" ]; then set -a; . "$ROOT_ENV"; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY must be set (shell or repo-root .env)}"

field() { python3 -c "import json,sys; print(json.load(sys.stdin)$1)"; }

echo "==> docker compose up"
docker compose up -d --build

printf "==> waiting for n8n"
until curl -sf "$BASE/healthz/readiness" >/dev/null 2>&1; do printf "."; sleep 2; done; echo " ready"

JAR="$(mktemp)"; trap 'rm -f "$JAR"' EXIT
rest() { curl -sf -b "$JAR" -c "$JAR" -H 'Content-Type: application/json' -H "browser-id: $BROWSER_ID" -X "$1" "$BASE/rest$2" ${3:+-d "$3"}; }

echo "==> owner account"
signed_in=""
for _ in $(seq 1 20); do
  if rest POST /owner/setup "{\"email\":\"$OWNER_EMAIL\",\"firstName\":\"Volunteer\",\"lastName\":\"Coordinator\",\"password\":\"$OWNER_PASSWORD\"}" >/dev/null 2>&1 \
     || rest POST /login "{\"emailOrLdapLoginId\":\"$OWNER_EMAIL\",\"password\":\"$OWNER_PASSWORD\"}" >/dev/null 2>&1; then
    signed_in=1; break
  fi
  sleep 2
done
[ -n "$signed_in" ] || { echo "could not sign in to n8n" >&2; exit 1; }

echo "==> public API key"
N8N_KEY=$(rest POST /api-keys '{"label":"riverbend-setup","expiresAt":null,"scopes":["workflow:create","workflow:read","workflow:delete","workflow:list","workflow:activate","credential:create","execution:read","execution:list"]}' | field "['data']['rawApiKey']")
api() { curl -sf -H "X-N8N-API-KEY: $N8N_KEY" -H 'Content-Type: application/json' -X "$1" "$BASE/api/v1$2" ${3:+-d "$3"}; }

echo "==> OpenAI credential"
CRED_ID=$(api POST /credentials "$(python3 -c 'import json,os; print(json.dumps({"name":"OpenAI (volunteer screening)","type":"openAiApi","data":{"apiKey":os.environ["OPENAI_API_KEY"]}}))')" | field "['id']")

echo "==> workflow"
api GET "/workflows?name=Volunteer%20screening" | python3 -c "import json,sys; [print(w['id']) for w in json.load(sys.stdin).get('data',[])]" \
  | while read -r old; do api DELETE "/workflows/$old" >/dev/null; done
WF_ID=$(sed "s/__OPENAI_CREDENTIAL_ID__/$CRED_ID/" workflow/volunteer-screening.json | api POST /workflows "$(cat)" | field "['id']")
api POST "/workflows/$WF_ID/activate" >/dev/null

echo
echo "n8n:      $BASE  ($OWNER_EMAIL / $OWNER_PASSWORD)"
echo "webhook:  $BASE/webhook/volunteer-signup"
echo "next:     ./demo.sh"
