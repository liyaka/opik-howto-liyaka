import opik
import pytest
from llama_index.core import Settings


@pytest.fixture(autouse=True)
def tracing_off(monkeypatch):
    # LlamaIndexCallbackHandler still sends traces when OPIK_TRACK_DISABLE is set,
    # so tests empty the callback manager's handler list and switch @opik.track off.
    monkeypatch.setattr(Settings.callback_manager, "handlers", [])
    opik.set_tracing_active(False)
    yield
    opik.set_tracing_active(True)
