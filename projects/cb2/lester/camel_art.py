"""Optional art loader for Standard Camel — terminal fallback chain."""
import os
import shutil
import subprocess

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ART_DIR = os.path.join(_SCRIPT_DIR, "camel", "graphics", "out")


def art_path(slot: str):
    for name in (f"{slot}.png", f"{slot}.jpg", f"{slot}.webp"):
        path = os.path.join(ART_DIR, name)
        if os.path.isfile(path):
            return path
    return None


def _terminal_image(path: str) -> bool:
    term = os.environ.get("TERM", "")
    if not term or term == "dumb":
        return False
    for cmd in (
        ["chafa", "-c", "none", path],
        ["imgcat", path],
        ["kitty", "+kitten", "icat", path],
    ):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(
                    cmd,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except OSError:
                continue
    return False


def show_slot(slot: str, fallback: str = "") -> None:
    path = art_path(slot)
    if path and _terminal_image(path):
        return
    if fallback:
        print(fallback)
