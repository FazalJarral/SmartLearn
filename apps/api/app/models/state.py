from enum import StrEnum


class ProcessingStage(StrEnum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    GENERATING_CONTENT = "generating_content"
    CONTENT_READY = "content_ready"
    GENERATING_AUDIO = "generating_audio"
    RENDERING_VIDEO = "rendering_video"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    DELETED = "deleted"


ALLOWED_TRANSITIONS: dict[ProcessingStage, set[ProcessingStage]] = {
    ProcessingStage.UPLOADED: {ProcessingStage.VALIDATING, ProcessingStage.DELETED},
    ProcessingStage.VALIDATING: {ProcessingStage.EXTRACTING, ProcessingStage.FAILED, ProcessingStage.DELETED},
    ProcessingStage.EXTRACTING: {ProcessingStage.GENERATING_CONTENT, ProcessingStage.FAILED, ProcessingStage.DELETED},
    ProcessingStage.GENERATING_CONTENT: {ProcessingStage.CONTENT_READY, ProcessingStage.FAILED, ProcessingStage.DELETED},
    ProcessingStage.CONTENT_READY: {ProcessingStage.GENERATING_AUDIO, ProcessingStage.RENDERING_VIDEO, ProcessingStage.COMPLETED, ProcessingStage.DELETED},
    ProcessingStage.GENERATING_AUDIO: {ProcessingStage.RENDERING_VIDEO, ProcessingStage.PARTIAL_SUCCESS, ProcessingStage.DELETED},
    ProcessingStage.RENDERING_VIDEO: {ProcessingStage.COMPLETED, ProcessingStage.PARTIAL_SUCCESS, ProcessingStage.FAILED, ProcessingStage.DELETED},
    ProcessingStage.COMPLETED: {ProcessingStage.DELETED},
    ProcessingStage.PARTIAL_SUCCESS: {ProcessingStage.RENDERING_VIDEO, ProcessingStage.DELETED},
    ProcessingStage.FAILED: {ProcessingStage.VALIDATING, ProcessingStage.GENERATING_CONTENT, ProcessingStage.RENDERING_VIDEO, ProcessingStage.DELETED},
    ProcessingStage.DELETED: set(),
}


def can_transition(current: ProcessingStage, target: ProcessingStage) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
