import os

# Keep unit tests off the Opik server: @opik.track and track_openai become no-ops.
os.environ["OPIK_TRACK_DISABLE"] = "true"
