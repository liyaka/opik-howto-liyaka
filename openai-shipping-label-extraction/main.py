"""Shipping-label field extraction with gpt-4o-mini vision, traced and tested with Opik.

The app draws six fictional labels with Pillow (some deliberately hard), sends
each image to gpt-4o-mini, and gets nine typed fields back. Every extraction is
an Opik trace with the label image attached, so the pixels the model saw sit
next to the fields it returned. An Opik test suite then checks each label
against assertions that carry the true values, and reports honest failures.
"""

import base64
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_NAME = "openai-shipping-label-extraction"
HERE = Path(__file__).parent

load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

# Use the public OpenAI API even if a local proxy override is inherited.
os.environ.pop("OPENAI_BASE_URL", None)
# Every trace, span and experiment from this process goes to one named project.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import opik  # noqa: E402
from openai import OpenAI  # noqa: E402
from opik import Attachment, opik_context  # noqa: E402
from opik.integrations.openai import track_openai  # noqa: E402

from labels import LABELS, OUT_DIR, render_all  # noqa: E402

# track_openai wraps the client: each completion becomes an llm span nested
# under the calling trace, with token usage (image tokens included) and cost.
openai_client = track_openai(OpenAI(), project_name=PROJECT_NAME)

MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """\
You read photos of parcel shipping labels and extract nine fields. Use only
what is printed or handwritten on the image. If a field is cut off or
unreadable, return an empty string (or 0 for weight) rather than guessing.

- carrier: the carrier name in the header.
- tracking_number: the human-readable tracking number printed under the barcode,
  exactly as written, including spaces and dashes.
- service_level: the service tier shown on the label (Ground, Express, ...).
- sender_name: the business under FROM.
- recipient_name, recipient_address, recipient_postcode: the SHIP TO block.
  The address is street and town on one line, without the postcode.
- weight_kg: the weight as a number in kilograms.
- ship_date: the ship date normalized to YYYY-MM-DD."""

STRING_FIELDS = [
    "carrier", "tracking_number", "service_level", "sender_name",
    "recipient_name", "recipient_address", "recipient_postcode", "ship_date",
]
FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        **{name: {"type": "string"} for name in STRING_FIELDS},
        "weight_kg": {"type": "number"},
    },
    "required": [*STRING_FIELDS, "weight_kg"],
    "additionalProperties": False,
}


def build_messages(image_b64: str) -> list[dict[str, Any]]:
    """Chat messages for one label: system prompt plus the image as a data URL."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract the fields from this shipping label."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                },
            ],
        },
    ]


# @opik.track opens the trace for one extraction; the llm span from track_openai
# nests inside it, so the trace tree is extract_label -> chat_completion_create.
@opik.track(project_name=PROJECT_NAME)
def extract_label(image: str) -> dict[str, Any]:
    """One traced extraction: label image in, nine typed fields out."""
    path = HERE / image
    image_b64 = base64.b64encode(path.read_bytes()).decode()

    # The attachment is uploaded with the trace: in the Opik UI the PNG the
    # model received is previewable next to the fields it returned.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(path), content_type="image/png")]
    )

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=build_messages(image_b64),
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "label_fields", "strict": True, "schema": FIELDS_SCHEMA},
        },
    )
    return json.loads(response.choices[0].message.content)


# --- The test suite: format rules for every label, true values per label ---------

# Judged from the output alone, for every label.
GLOBAL_ASSERTIONS = [
    "All nine fields are present in the output",
    "ship_date is in YYYY-MM-DD format and weight_kg is a number",
    "No field contains a placeholder such as 'unknown', 'N/A' or 'null'; a field "
    "the label does not show is an empty string",
]


def build_assertions(label: dict[str, Any]) -> list[str]:
    """Two plain-language assertions carrying the true values for one label."""
    return [
        f"The carrier is {label['carrier']}, the service level is {label['service_level']} "
        f"and the sender is {label['sender_name']}",
        f"The tracking number is exactly '{label['tracking_number']}' and the ship date "
        f"is {label['ship_date']}",
        f"The recipient is {label['recipient_name']} at {label['recipient_address']}, "
        f"postcode {label['recipient_postcode']}, and the weight is {label['weight_kg']} kg",
    ]


def build_items(images: dict[str, Path]) -> list[dict[str, Any]]:
    """Suite items: the image path is the input, the truth lives in the assertions."""
    return [
        {
            "data": {"image": str(images[lb["id"]].relative_to(HERE)), "kind": lb["kind"]},
            "assertions": build_assertions(lb),
        }
        for lb in LABELS
    ]


def main() -> None:
    print(f"Rendering {len(LABELS)} fictional labels into out/ ...")
    images = render_all(OUT_DIR)

    client = opik.Opik()
    # A test suite = global assertions + per-item assertions, judged by an LLM.
    # runs_per_item=3 / pass_threshold=2 re-runs each label three times and
    # passes it on two, which absorbs one-off extraction and judge noise.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    suite.insert(build_items(images))

    def extraction_task(item: dict[str, Any]) -> dict[str, Any]:
        return {"input": item, "output": extract_label(item["image"])}

    # run_tests runs the task over every item, has the judge grade each
    # assertion, and records one experiment whose traces are linked to the items.
    result = opik.run_tests(
        test_suite=suite,
        task=extraction_task,
        experiment_name="label-extraction-gpt-4o-mini",
        worker_threads=3,
        generate_report=False,
    )

    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} labels)")
    for item_result in result.item_results.values():
        image = item_result.test_results[0].test_case.task_output["input"]["image"]
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {image}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")

    # Traces and attachments upload in the background; flush before exiting.
    client.flush()
    opik.flush_tracker()


if __name__ == "__main__":
    main()
