#!/usr/bin/env bash
# Starts the service, asks a few scripted questions over HTTP, then shuts it down.
set -euo pipefail
cd "$(dirname "$0")"

for env_file in ../.env .env; do
  if [[ -f "$env_file" ]]; then
    set -a; source "$env_file"; set +a
  fi
done
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY (see .env.example)}"

PORT=3291
./mvnw -q -DskipTests package

java -jar target/quarkus-app/quarkus-run.jar > target/app.log 2>&1 &
APP_PID=$!
trap 'kill $APP_PID 2>/dev/null || true' EXIT

for _ in $(seq 1 60); do
  curl -s -o /dev/null "http://localhost:$PORT/" && break
  sleep 1
done

QUESTIONS=(
  "How much Nuvelin can I take in a day?"
  "Can I drink grapefruit juice while taking Corbexol?"
  "How should I store Glycavora?"
  "Is it okay to take Veltrazine together with Dormaxin?"
  "Can I take Zentorin for my headaches?"
)
for q in "${QUESTIONS[@]}"; do
  echo "Q: $q"
  echo "A: $(curl -fsS --get --data-urlencode "q=$q" "http://localhost:$PORT/ask")"
  echo
done

kill "$APP_PID"
wait "$APP_PID" 2>/dev/null || true
trap - EXIT
