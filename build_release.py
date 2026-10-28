"""
Builds the app with PyInstaller and assembles a ready-to-copy folder:

    release/Rostek/
        RoasterInterface.exe
        _internal/          (Python, Kivy, ui, assets - read-only)
        config.json         (simulation OFF, PLC IP placeholder, no MQTT secrets)
        profiles/           (copied from this project)
        KURULUM.txt
    release/Rostek-<version>.zip   (same folder zipped, for GitHub Releases)

Run with the project venv:  venv\\Scripts\\python.exe build_release.py [version]
(or just double-click build.bat). Version defaults to today's date.

release/Rostek is recreated from scratch on every build. Do not keep the
machine's real config/profiles there; they live on the target PC.

The GitHub repo is public, so the zip must never contain MQTT credentials:
username/password are left empty and entered on the target PC.
"""
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "RoasterInterface.spec"
DIST = ROOT / "dist" / "RoasterInterface"
OUT = ROOT / "release" / "Rostek"

# Placeholder until the real PLC address is known (edit config.json on the PC)
PLC_IP_PLACEHOLDER = "192.168.1.50"


def step(msg):
    print(f"\n=== {msg} ===", flush=True)


def build_exe():
    step("PyInstaller")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(SPEC), "--noconfirm", "--clean"],
        cwd=ROOT,
        check=True,
    )
    if not (DIST / "RoasterInterface.exe").exists():
        sys.exit("Build failed: dist/RoasterInterface/RoasterInterface.exe not found")


def assemble():
    step(f"Assembling {OUT}")
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(DIST, OUT)

    # profiles are read/written next to the exe (not from _internal)
    shutil.copytree(ROOT / "profiles", OUT / "profiles")

    # config.json: real machine settings, simulation always OFF
    cfg = {}
    try:
        cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    except Exception as e:
        print(f"config.json not read ({e}), using defaults")

    modbus = dict(cfg.get("modbus", {}))
    modbus["host"] = PLC_IP_PLACEHOLDER
    modbus.setdefault("port", 502)
    modbus.setdefault("unit_id", 2)
    modbus.setdefault("timeout", 1.5)

    # keep broker/port, never ship credentials (zip is downloadable by anyone)
    mqtt_src = cfg.get("mqtt", {})
    mqtt = {
        "broker": mqtt_src.get("broker", ""),
        "port": mqtt_src.get("port", 8883),
        "username": "",
        "password": "",
    }

    release_cfg = {
        "simulation": False,
        "modbus": modbus,
        "mqtt": mqtt,
    }
    (OUT / "config.json").write_text(
        json.dumps(release_cfg, ensure_ascii=False, indent=4), encoding="utf-8"
    )

    shutil.copy2(ROOT / "KURULUM.txt", OUT / "KURULUM.txt")


def make_zip(version):
    step("Zip")
    base = OUT.parent / f"Rostek-{version}"
    zip_path = Path(shutil.make_archive(str(base), "zip", root_dir=OUT.parent, base_dir=OUT.name))
    print(f"{zip_path}  ({zip_path.stat().st_size / 1e6:.0f} MB)")
    return zip_path


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    build_exe()
    assemble()
    zip_path = make_zip(version)
    step("Done")
    print(f"Folder: {OUT}")
    print(f"Zip   : {zip_path}  -> upload to GitHub Releases")
    print(f"PLC IP in config.json is a placeholder: {PLC_IP_PLACEHOLDER}")
    print("MQTT username/password are empty: enter them on the target PC")


if __name__ == "__main__":
    main()
