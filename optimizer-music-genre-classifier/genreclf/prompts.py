"""The deliberately loose first-draft prompt."""

# Names the genres in prose, never says how to answer, gives no tie-breaks.
BASELINE_SYSTEM = """\
You help a radio station tag its catalogue. Read the description of a song
and work out which kind of music it is: classical, jazz, folk, metal,
electronic or hip-hop. Give us the genre."""

# {song} is filled from the dataset's "song" field.
USER_TEMPLATE = "{song}"


def baseline_messages() -> list[dict]:
    return [
        {"role": "system", "content": BASELINE_SYSTEM},
        {"role": "user", "content": USER_TEMPLATE},
    ]
