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
                "definitions": [
                    {
                        "term": f"Term {i}",
                        "definition": "A simple definition stated in everyday language.",
                        "example": "A concrete example showing the idea in use.",
                        "source_pages": [1],
                    }
                    for i in range(1, 4)
                ],
            },
            "topics": [
                {
                    "name": f"Topic {i}",
                    "description": "A topic identified in the uploaded material.",
                    "source_pages": [1],
                    "further_learning": [
                        {
                            "title": "Watch a visual introduction",
                            "resource_type": "video",
                            "search_query": f"Topic {i} visual introduction for beginners",
                            "why_it_helps": "Build intuition with a second visual explanation.",
                        }
                    ],
                }
                for i in range(1, 4)
            ],
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
                "title": "How the key idea works",
                "narration": "First, meet the key idea. Then see how its parts connect, follow the process, and use it in a concrete example before bringing the explanation together.",
                "scenes": [
                    {
                        "template": "intro",
                        "heading": "Meet the key idea",
                        "visual_elements": ["Key idea", "Question"],
                        "narration": "Start with the central question and the key idea that answers it.",
                        "duration_seconds": 8,
                    },
                    {
                        "template": "concept_map",
                        "heading": "Connect the parts",
                        "visual_elements": ["Key idea", "Part A", "Part B"],
                        "connection_label": "connects",
                        "narration": "The key idea becomes clearer when we connect its two main parts.",
                        "duration_seconds": 12,
                    },
                    {
                        "template": "process",
                        "heading": "Follow the process",
                        "visual_elements": ["Input", "Change", "Result"],
                        "connection_label": "becomes",
                        "narration": "Now follow the idea from an input, through a change, to its result.",
                        "duration_seconds": 12,
                    },
                    {
                        "template": "worked_example",
                        "heading": "See it in action",
                        "visual_elements": ["Example", "Apply idea", "Answer"],
                        "narration": "A concrete example shows when to use the idea and what result to expect.",
                        "duration_seconds": 12,
                    },
                ],
            },
        }
    )
