"""The Opik prompt library: baseline as version 1, optimizer winner after it."""

import opik

from genreclf.config import LIBRARY_PROMPT_NAME, PROJECT_NAME
from genreclf.prompts import baseline_messages


def to_mustache(messages: list[dict]) -> list[dict]:
    """The optimizer writes {song}; the library's mustache format wants {{song}}."""
    return [
        {**m, "content": m["content"].replace("{song}", "{{song}}")}
        for m in messages
    ]


def save_baseline(client: opik.Opik):
    # create_chat_prompt stores a versioned prompt in the library, scoped to the
    # project. Saving the baseline first makes the library tell the whole
    # story: v1 hand-written, v2 optimizer winner. Identical content adds no version.
    return client.create_chat_prompt(
        name=LIBRARY_PROMPT_NAME,
        messages=to_mustache(baseline_messages()),
        change_description="Baseline hand-written prompt (pre-optimization)",
        metadata={"source": "hand-written baseline"},
        project_name=PROJECT_NAME,
    )


def save_winner(client: opik.Opik, messages: list[dict], change_description: str, metadata: dict):
    # A new version of the same prompt name: the Prompt library shows it next
    # to the baseline with the diff. The scores go in `metadata`, which this
    # server stores and returns; `change_description` comes back as None here.
    return client.create_chat_prompt(
        name=LIBRARY_PROMPT_NAME,
        messages=to_mustache(messages),
        change_description=change_description,
        metadata=metadata,
        project_name=PROJECT_NAME,
    )


def versions(client: opik.Opik) -> list:
    """Every saved version of the prompt, newest first."""
    return client.get_chat_prompt_history(LIBRARY_PROMPT_NAME, project_name=PROJECT_NAME)
