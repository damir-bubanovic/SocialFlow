from socialflow.ui.posts.language_selector import LanguageSelector
from socialflow.domain.language.language import Language


def test_language_selector_has_supported_languages(qtbot) -> None:
    selector = LanguageSelector()
    qtbot.addWidget(selector)

    assert selector.count() == 2
    assert selector.itemData(0) == Language.CROATIAN
    assert selector.itemData(1) == Language.ENGLISH


def test_croatian_is_default_language(qtbot) -> None:
    selector = LanguageSelector()
    qtbot.addWidget(selector)

    assert selector.selected_language() == Language.CROATIAN


def test_language_can_be_changed(qtbot) -> None:
    selector = LanguageSelector()
    qtbot.addWidget(selector)

    selector.setCurrentIndex(1)

    assert selector.selected_language() == Language.ENGLISH