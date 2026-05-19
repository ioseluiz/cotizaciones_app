import sys
import os


def resource_path(relative_path: str) -> str:
    """Return absolute path to a resource, compatible with PyInstaller bundles."""
    try:
        base = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
