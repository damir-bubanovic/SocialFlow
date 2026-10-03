from socialflow.ui.navigation import Navigation


def test_navigation_has_expected_sections(qtbot) -> None:
    navigation = Navigation()
    qtbot.addWidget(navigation)

    assert navigation.tab_bar.count() == 3
    assert navigation.tab_bar.tabText(Navigation.POSTS_INDEX) == "Posts"
    assert navigation.tab_bar.tabText(Navigation.ACCOUNTS_INDEX) == "Accounts"
    assert navigation.tab_bar.tabText(Navigation.SETTINGS_INDEX) == "Settings"


def test_posts_is_default_navigation_section(qtbot) -> None:
    navigation = Navigation()
    qtbot.addWidget(navigation)

    assert navigation.tab_bar.currentIndex() == Navigation.POSTS_INDEX