from app.services.deepseek_generation import extract_json_object, normalize_study_package_payload


def test_extract_json_object_accepts_plain_json():
    assert extract_json_object('{"schema_version":"1.0"}') == {"schema_version": "1.0"}


def test_extract_json_object_accepts_fenced_json():
    assert extract_json_object('```json\n{"schema_version":"1.0"}\n```') == {"schema_version": "1.0"}


def test_extract_json_object_finds_wrapped_json():
    assert extract_json_object('Here is json: {"schema_version":"1.0"} done') == {
        "schema_version": "1.0"
    }


def test_normalize_study_package_payload_clamps_scene_durations():
    payload = {"video": {"scenes": [{"duration_seconds": 14}, {"duration_seconds": 2}]}}

    normalized = normalize_study_package_payload(payload)

    assert normalized["video"]["scenes"][0]["duration_seconds"] == 12
    assert normalized["video"]["scenes"][1]["duration_seconds"] == 3
