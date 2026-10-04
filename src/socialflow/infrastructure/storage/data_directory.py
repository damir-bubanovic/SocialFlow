import os
import sys
from pathlib import Path


def data_directory() -> Path:
    """Return the platform-specific SocialFlow data directory."""
    if sys.platform == "win32":
        app_data = os.environ.get("LOCALAPPDATA")

        if app_data:
            return Path(app_data) / "SocialFlow"

        return Path.home() / "AppData" / "Local" / "SocialFlow"

    xdg_data_home = os.environ.get("XDG_DATA_HOME")

    if xdg_data_home:
        return Path(xdg_data_home) / "socialflow"

    return Path.home() / ".local" / "share" / "socialflow"