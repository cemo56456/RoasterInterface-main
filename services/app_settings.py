import json
import os

from services.config import _app_dir


def _path():
    return os.path.join(_app_dir(), "settings.json")


def load_settings() -> dict:
    """Returns the saved settings dict ({} if the file is missing or broken)."""
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[Settings] failed to load {_path()}: {e}")
        return {}


def save_settings(values: dict) -> tuple:
    """
    Merges `values` into settings.json and writes it atomically
    (temp file + replace, so a crash never leaves a half-written file).
    Returns (ok, err).
    """
    path = _path()
    tmp = path + ".tmp"
    try:
        data = load_settings()
        data.update(values)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return True, None
    except Exception as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False, str(e)
