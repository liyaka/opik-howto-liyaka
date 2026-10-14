"""Four fictional voicemails for the Maple Hollow Veterinary Clinic.

Every name, pet and phone number is invented (555-01xx numbers are reserved
for fiction). Each script is spoken by OpenAI TTS at run time, so no audio is
committed. `expected` is what a sensible receptionist would decide.
"""

VOICEMAILS = [
    {
        "id": "biscuit-xylitol",
        "caller": "Dana Okafor",
        "voice": "nova",
        "expected": "emergency",
        "script": (
            "Hi, this is Dana Okafor. My dog Biscuit just ate a whole pack of "
            "sugar-free gum and now he's vomiting and wobbling when he walks. "
            "Please call me right away on five five five, zero one four two."
        ),
    },
    {
        "id": "juniper-paw",
        "caller": "Marcus Lindqvist",
        "voice": "onyx",
        "expected": "same-day",
        "script": (
            "Hello, Marcus Lindqvist here. My cat Juniper has been limping "
            "since this morning and her back paw looks swollen. She's still "
            "eating and purring. Could someone ring me today on five five "
            "five, zero one seven seven?"
        ),
    },
    {
        "id": "clover-checkup",
        "caller": "Priya Raman",
        "voice": "shimmer",
        "expected": "routine",
        "script": (
            "Hi, it's Priya Raman. I'd like to book the yearly checkup and "
            "vaccines for my rabbit Clover, sometime in the next few weeks. "
            "No rush at all. My number is five five five, zero one one nine."
        ),
    },
    {
        "id": "pickles-quiet",
        "caller": "Elena Voss",
        "voice": "echo",
        "expected": "same-day",
        "script": (
            "Hey, Elena Voss. It's probably nothing and there's no hurry, "
            "but my parrot Pickles has been fluffed up and quiet and hasn't "
            "touched his food in two days. Call me on five five five, zero "
            "one six three."
        ),
    },
]
