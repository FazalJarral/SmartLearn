from app.models.state import ProcessingStage, can_transition


def test_state_machine_allows_expected_progression():
    assert can_transition(ProcessingStage.UPLOADED, ProcessingStage.VALIDATING)
    assert can_transition(ProcessingStage.CONTENT_READY, ProcessingStage.RENDERING_VIDEO)
    assert can_transition(ProcessingStage.RENDERING_VIDEO, ProcessingStage.PARTIAL_SUCCESS)


def test_deleted_is_terminal():
    assert not can_transition(ProcessingStage.DELETED, ProcessingStage.VALIDATING)
