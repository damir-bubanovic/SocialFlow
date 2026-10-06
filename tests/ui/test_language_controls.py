from socialflow.domain.language.language import Language
from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.ui.posts.language_indicator import LanguageIndicator
from socialflow.ui.posts.language_selector import LanguageSelector


def test_language_controls_contains_selector_and_indicator(qtbot) -> None:
    controls = LanguageControls()
    qtbot.addWidget(controls)

    assert isinstance(controls.selector, LanguageSelector)
    assert isinstance(controls.indicator, LanguageIndicator)


def test_language_controls_defaults_to_croatian(qtbot) -> None:
    controls = LanguageControls()
    qtbot.addWidget(controls)

    assert controls.selected_language() == Language.CROATIAN
    assert controls.indicator.text() == "HR"


def test_language_controls_updates_indicator(qtbot) -> None:
    controls = LanguageControls()
    qtbot.addWidget(controls)

    controls.selector.setCurrentIndex(1)

    assert controls.selected_language() == Language.ENGLISH
    assert controls.indicator.text() == "EN"

def test_language_controls_can_set_language(qtbot) -> None:
    controls = LanguageControls()
    qtbot.addWidget(controls)

    controls.set_language(Language.ENGLISH)

    assert controls.selected_language() == Language.ENGLISH