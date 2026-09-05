from app.services.deepseek_generation import extract_json_object


def test_extract_json_object_accepts_plain_json():
    assert extract_json_object('{"schema_version":"1.0"}') == {"schema_version": "1.0"}


def test_extract_json_object_accepts_fenced_json():
    assert extract_json_object('```json\n{"schema_version":"1.0"}\n```') == {"schema_version": "1.0"}


def test_extract_json_object_finds_wrapped_json():
    assert extract_json_object('Here is json: {"schema_version":"1.0"} done') == {
        "schema_version": "1.0"
    }
