from socialflow.domain.language.language import Language


def test_supported_language_codes() -> None:
    assert Language.CROATIAN == "HR"
    assert Language.ENGLISH == "EN"

def test_language_display_names() -> None:
    assert Language.CROATIAN.display_name == "Croatian"
    assert Language.ENGLISH.display_name == "English"

def test_language_labels() -> None:
    assert Language.CROATIAN.label == "HR - Croatian"
    assert Language.ENGLISH.label == "EN - English"