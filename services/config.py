import json
import os
import sys

DEFAULTS = {
    "modbus": {
        "host": "192.168.1.50",
        "port": 502,
        "unit_id": 2,
        "timeout": 1.5,
    },
    "mqtt": {
        "broker": "",
        "port": 8883,
        "username": "",
        "password": "",
    },
}


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    """
    Loads config.json from the app directory. Falls back to DEFAULTS
    (with empty MQTT credentials) if the file is missing or invalid,
    so a missing config never silently reuses a baked-in secret.
    """
    path = os.path.join(_app_dir(), "config.json")

    config = {
        "modbus": dict(DEFAULTS["modbus"]),
        "mqtt": dict(DEFAULTS["mqtt"]),
    }

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for section in ("modbus", "mqtt"):
            if section in data:
                config[section].update(data[section])

        config["simulation"] = bool(data.get("simulation", False))

    except FileNotFoundError:
        print(f"[Config] {path} not found, using defaults")
    except Exception as e:
        print(f"[Config] failed to load {path}: {e}")

    return config
