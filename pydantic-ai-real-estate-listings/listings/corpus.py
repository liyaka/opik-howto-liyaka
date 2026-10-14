"""Fictional notes the agent must parse, plus plain-language assertions per note.

Expected values live in the assertions, never in the note data.
"""

GLOBAL_ASSERTIONS = [
    "The output is a complete listing record with the fields address, price_usd, "
    "bedrooms, bathrooms, square_feet, year_built, agent_name, agent_phone and agent_email",
    "Every non-null value in the output is present in, or directly derivable from, the note",
    "No value is invented: fields the note does not mention are null",
    "If agent_email is not null, it looks like a valid email address",
]

ITEMS = [
    {
        "note": (
            "NEW LISTING 412 Alder Lane, Fairhaven OR. 3bd/2ba, 1,640 sqft, built 1994. "
            "Asking $489,000. Call Renata Okafor 541-555-0187 or renata@harborlight-homes.example"
        ),
        "assertions": [
            "The address is 412 Alder Lane and the price is 489000",
            "Bedrooms is 3, bathrooms is 2 and square_feet is 1640",
            "The agent is Renata Okafor with email renata@harborlight-homes.example",
        ],
    },
    {
        "note": (
            "[voicemail] hey its Gus Brandt, uh, got a new one, 88 Tern Street, "
            "its a four bedroom, two and a half bath, asking uh four seventy five... "
            "four seventy-five thousand. Call me back at five five five, oh one six two."
        ),
        "assertions": [
            "The price is 475000, bedrooms is 4 and bathrooms is 2.5",
            "The agent name is Gus Brandt and the phone is 555-0162",
            "The email is null because the caller never gives one",
            "Square footage and year built are null because the voicemail never states them",
        ],
    },
    {
        "note": "txt from Mei: 9 Quarry Rd unit B is a 1bd condo 2/3 of a mile from the ferry, 3-something hundred k? will confirm",
        "assertions": [
            "The address is 9 Quarry Rd unit B and bedrooms is 1",
            "The price is null because the note gives only a vague range, not a figure",
            "The agent name is Mei",
        ],
    },
    {
        "note": (
            "1180 Saltmarsh Ct. Beautiful brick colonial, huge lot, new roof 2021. "
            "4 beds 3 baths. $1.2M. Showings w/ Dolores at dolores.v (at) tidewater-realty.example"
        ),
        "assertions": [
            "The price is 1200000 and bedrooms is 4 and bathrooms is 3",
            "The year built is null, since 2021 is only the roof date",
            "The agent email is dolores.v@tidewater-realty.example, decoded from the '(at)' obfuscation",
        ],
    },
    {
        "note": "open house sun 2-4 at 27 Wren Hollow!! cute starter, 2bd 1ba ~900 sq ft. lmk -Theo 503 555 0144",
        "assertions": [
            "The address is 27 Wren Hollow, bedrooms is 2 and bathrooms is 1",
            "The agent is Theo and the phone digits are 5035550144, with any separators",
            "The price is null because no price is stated",
            "The agent email is null because the note contains none",
        ],
    },
    {
        "note": "Gutted to the studs, 61 Harlow Ave, priced to move at 310k. DM Priya for details.",
        "assertions": [
            "The address is 61 Harlow Ave and the price is 310000",
            "Bedrooms, bathrooms and square_feet are null because the note does not state them",
            "The agent name is Priya and phone and email are null",
        ],
    },
]


def resolve_note(arg: str) -> str:
    """A digit selects a bundled note (1-based); anything else is the note text itself."""
    return ITEMS[int(arg) - 1]["note"] if arg.isdigit() else arg
