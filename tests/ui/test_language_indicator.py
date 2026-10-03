from socialflow.domain.language.language import Language
from socialflow.ui.posts.language_indicator import LanguageIndicator


def test_language_indicator_defaults_to_croatian(qtbot) -> None:
    indicator = LanguageIndicator()
    qtbot.addWidget(indicator)

    assert indicator.text() == "HR"


def test_language_indicator_can_display_english(qtbot) -> None:
    indicator = LanguageIndicator()
    qtbot.addWidget(indicator)

    indicator.set_language(Language.ENGLISH)

    assert indicator.text() == "EN"

def test_croatian_language_has_distinct_style(qtbot) -> None:
    indicator = LanguageIndicator()
    qtbot.addWidget(indicator)

    indicator.set_language(Language.CROATIAN)

    assert indicator.property("language") == "HR"


def test_english_language_has_distinct_style(qtbot) -> None:
    indicator = LanguageIndicator()
    qtbot.addWidget(indicator)

    indicator.set_language(Language.ENGLISH)

    assert indicator.property("language") == "EN"