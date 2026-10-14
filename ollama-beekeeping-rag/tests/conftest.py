import os

# Must be set before opik is imported so no test can write traces.
os.environ["OPIK_TRACK_DISABLE"] = "true"
os.environ["OPIK_PROJECT_NAME"] = "ollama-beekeeping-rag-tests"
