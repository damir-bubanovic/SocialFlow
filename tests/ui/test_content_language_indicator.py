from socialflow.application.language.post_language_classifier import (
    PostLanguageClassification,
)
from socialflow.ui.posts.content_language_indicator import (
    ContentLanguageIndicator,
)


def test_content_language_indicator_defaults_to_unknown(qtbot) -> None:
    indicator = ContentLanguageIndicator()
    qtbot.addWidget(indicator)

    assert indicator.text() == "?"


def test_content_language_indicator_displays_each_classification(qtbot) -> None:
    indicator = ContentLanguageIndicator()
    qtbot.addWidget(indicator)

    expected_labels = {
        PostLanguageClassification.ENGLISH: "EN",
        PostLanguageClassification.CROATIAN: "HR",
        PostLanguageClassification.MIXED: "HR + EN",
        PostLanguageClassification.UNKNOWN: "?",
    }

    for classification, expected_label in expected_labels.items():
        indicator.set_classification(classification)
        assert indicator.text() == expected_label

def test_content_language_indicator_updates_color(qtbot) -> None:
    indicator = ContentLanguageIndicator()
    qtbot.addWidget(indicator)

    assert "#6b7280" in indicator.styleSheet()

    expected_colors = {
        PostLanguageClassification.ENGLISH: "#16a34a",
        PostLanguageClassification.CROATIAN: "#2563eb",
        PostLanguageClassification.MIXED: "#9333ea",
        PostLanguageClassification.UNKNOWN: "#6b7280",
    }

    for classification, expected_color in expected_colors.items():
        indicator.set_classification(classification)

        assert expected_color in indicator.styleSheet()

def test_content_language_indicator_has_accessible_description(qtbot) -> None:
    indicator = ContentLanguageIndicator()
    qtbot.addWidget(indicator)

    assert indicator.accessibleName() == "Detected content language"

    indicator.set_classification(
        PostLanguageClassification.MIXED
    )

    assert (
        indicator.accessibleDescription()
        == "Detected content language: HR + EN"
    )