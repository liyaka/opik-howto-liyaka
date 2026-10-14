# openai-ts-museum-visitor-desk

A visitor-desk chatbot for a fictional museum, built on the OpenAI Node SDK and traced with Opik: one thread per conversation, a trace per turn, and a satisfaction score logged after the run.

## Run it

1. `npm install`
2. Put `OPENAI_API_KEY` in `.env` (or the repo-root `.env`); set `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE` for your Opik.
3. `npm run demo`
4. `npm run verify` reads the project back from Opik.

## Tests

`npm test` runs offline with a stubbed client; `OPIK_TRACK_DISABLE=true` turns the Opik SDK into a no-op.
