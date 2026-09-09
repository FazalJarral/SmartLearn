import asyncio

from app.core.errors import ApiError
from app.services.deepseek_generation import (
    DeepSeekStudyPackageGenerator,
    GenerationInput,
    extract_json_object,
    normalize_study_package_payload,
)


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

    assert normalized["video"]["scenes"][0]["duration_seconds"] == 14
    assert normalized["video"]["scenes"][1]["duration_seconds"] == 6


def test_normalize_study_package_payload_caps_total_video_duration():
    payload = {"video": {"scenes": [{"duration_seconds": 20} for _ in range(6)]}}

    normalized = normalize_study_package_payload(payload)

    assert sum(scene["duration_seconds"] for scene in normalized["video"]["scenes"]) == 90


def test_generator_retries_transient_empty_response(monkeypatch):
    generator = object.__new__(DeepSeekStudyPackageGenerator)
    calls = 0

    async def fake_chat(_messages):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ApiError("deepseek_empty_response", "empty", 502)
        from app.services.mock_generation import mock_study_package

        return mock_study_package().model_dump_json()

    monkeypatch.setattr(generator, "_chat", fake_chat)
    result = asyncio.run(generator.generate(GenerationInput("lesson.pdf", 1, "lesson text")))

    assert result.title == "Uploaded Document"
    assert calls == 2
