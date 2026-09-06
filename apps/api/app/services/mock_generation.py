from app.schemas.content import StudyPackage


def mock_study_package(title: str = "Uploaded Document") -> StudyPackage:
    return StudyPackage.model_validate(
        {
            "schema_version": "1.0",
            "title": title,
            "summary": {
                "overview": "A concise mock overview used while provider integrations are disabled.",
                "key_points": [
                    {"heading": f"Concept {i}", "explanation": "Grounded explanation placeholder.", "source_pages": [1]}
                    for i in range(1, 6)
                ],
            },
            "flashcards": [
                {"front": f"Cue {i}", "back": "Answer placeholder.", "source_pages": [1]}
                for i in range(1, 9)
            ],
            "quiz": [
                {
                    "question": f"Question {i}?",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0,
                    "explanation": "A is correct in mock mode.",
                    "source_pages": [1],
                }
                for i in range(1, 6)
            ],
            "video": {
                "title": "Mock Video",
                "narration": "This is placeholder narration for a short instructional video.",
                "scenes": [
                    {"template": "title", "text": ["Mock Video"], "duration_seconds": 5},
                    {
                        "template": "definition",
                        "text": ["A key idea", "A short explanation"],
                        "narration": "This first concept is the anchor idea. Learn it first, then connect details back to it.",
                        "duration_seconds": 10,
                    },
                    {
                        "template": "bullet_list",
                        "text": ["Review", "Recall", "Apply"],
                        "narration": "Use review, recall, and application to check whether the concept is actually understood.",
                        "duration_seconds": 10,
                    },
                ],
            },
        }
    )
