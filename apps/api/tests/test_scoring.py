from app.services.scoring import is_correct_answer


def test_correct_answer_matches_index() -> None:
    assert is_correct_answer(2, 2)


def test_incorrect_answer_does_not_match_index() -> None:
    assert not is_correct_answer(1, 2)
