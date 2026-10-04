from pathlib import Path

from socialflow.infrastructure.storage import data_directory as module


def test_data_directory_uses_xdg_data_home_on_linux(
    monkeypatch,
) -> None:
    monkeypatch.setattr(module.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/data")

    assert module.data_directory() == Path(
        "/tmp/data/socialflow"
    )


def test_data_directory_uses_default_linux_location(
    monkeypatch,
) -> None:
    monkeypatch.setattr(module.sys, "platform", "linux")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(
        module.Path,
        "home",
        lambda: Path("/home/testuser"),
    )

    assert module.data_directory() == Path(
        "/home/testuser/.local/share/socialflow"
    )


def test_data_directory_uses_local_app_data_on_windows(
    monkeypatch,
) -> None:
    monkeypatch.setattr(module.sys, "platform", "win32")
    monkeypatch.setenv(
        "LOCALAPPDATA",
        "C:/Users/Test/AppData/Local",
    )

    assert module.data_directory() == Path(
        "C:/Users/Test/AppData/Local/SocialFlow"
    )


def test_data_directory_has_windows_fallback(
    monkeypatch,
) -> None:
    monkeypatch.setattr(module.sys, "platform", "win32")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(
        module.Path,
        "home",
        lambda: Path("C:/Users/Test"),
    )

    assert module.data_directory() == Path(
        "C:/Users/Test/AppData/Local/SocialFlow"
    )