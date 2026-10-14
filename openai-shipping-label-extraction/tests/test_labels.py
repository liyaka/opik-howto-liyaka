import json
from types import SimpleNamespace

from PIL import Image

import main
from labels import LABELS, render_all


def test_label_ids_are_unique_and_complete():
    assert len({lb["id"] for lb in LABELS}) == len(LABELS)
    for lb in LABELS:
        for key in [*main.STRING_FIELDS, "weight_kg"]:
            assert key in lb


def test_render_all_writes_pngs(tmp_path):
    paths = render_all(tmp_path)
    assert set(paths) == {lb["id"] for lb in LABELS}
    for p in paths.values():
        assert Image.open(p).size[0] >= 700


def test_assertions_carry_the_true_values():
    lb = LABELS[0]
    text = " ".join(main.build_assertions(lb))
    for key in ("carrier", "tracking_number", "recipient_postcode", "ship_date"):
        assert lb[key] in text
    assert f"{lb['weight_kg']} kg" in text


def test_items_use_relative_image_paths(tmp_path):
    items = main.build_items({lb["id"]: main.HERE / "out" / f"{lb['id']}.png" for lb in LABELS})
    assert len(items) == len(LABELS)
    assert items[0]["data"]["image"] == "out/clean-ground.png"


def test_messages_embed_the_image_as_data_url():
    msgs = main.build_messages("QUJD")
    assert msgs[1]["content"][1]["image_url"]["url"] == "data:image/png;base64,QUJD"


def test_schema_requires_every_field():
    assert set(main.FIELDS_SCHEMA["required"]) == set(main.FIELDS_SCHEMA["properties"])


def test_traced_extract_label_with_tracking_disabled(tmp_path, monkeypatch):
    render_all(main.OUT_DIR)
    fields = {k: "x" for k in main.STRING_FIELDS} | {"weight_kg": 1.0}
    fake = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(fields)))]
    )
    stub = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: fake)))
    monkeypatch.setattr(main, "openai_client", stub)
    assert main.extract_label("out/clean-ground.png") == fields
