from dataclasses import dataclass


@dataclass(frozen=True)
class TtsResult:
    audio_path: str | None
    narration_available: bool
    error_message: str | None = None


class TtsProvider:
    def synthesize(self, text: str, output_dir: str) -> TtsResult:
        raise NotImplementedError


class DummyTtsProvider(TtsProvider):
    def synthesize(self, text: str, output_dir: str) -> TtsResult:
        _ = (text, output_dir)
        return TtsResult(audio_path=None, narration_available=False, error_message="Dummy TTS provider")
