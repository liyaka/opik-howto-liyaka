import os

# Set before opik is imported so the tests never send a trace.
os.environ["OPIK_TRACK_DISABLE"] = "true"
