import pytest
from pydantic import ValidationError

from app.services.mock_generation import mock_study_package


def test_mock_package_matches_schema():
    package = mock_study_package()
    assert package.schema_version == "1.0"
    assert len(package.flashcards) == 8
    assert len(package.quiz[0].options) == 4


def test_quiz_requires_four_options():
    data = mock_study_package().model_dump()
    data["quiz"][0]["options"] = ["A", "B", "C"]
    with pytest.raises(ValidationError):
        type(mock_study_package()).model_validate(data)
