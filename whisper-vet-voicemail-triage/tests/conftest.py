import os
import sys
from pathlib import Path

# Tracking off and a dummy key: the tests must never reach Opik or OpenAI.
os.environ["OPIK_TRACK_DISABLE"] = "true"
os.environ.setdefault("OPENAI_API_KEY", "test-key")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
