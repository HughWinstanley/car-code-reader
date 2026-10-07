#!/usr/bin/env python3
"""
Starts Car Code Reader. If a newer version has been downloaded by the in-app updater,
that copy is used; otherwise the installed copy next to this file is used.
This file itself is never replaced by updates.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ("car_code_reader.py", "obd_core.py", "dtc_database.py", "version.py")


def _updates_dir():
    if sys.platform == "darwin":
        root = os.path.expanduser("~/Library/Application Support/Car Code Reader")
    elif os.name == "nt":
        root = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Car Code Reader")
    else:
        root = os.path.expanduser("~/.car-code-reader")
    return os.path.join(root, "app")


def _version(folder):
    try:
        with open(os.path.join(folder, "version.py"), encoding="utf-8") as f:
            return tuple(int(x) for x in re.findall(r"\d+", f.read()))
    except OSError:
        return ()


def main():
    upd = _updates_dir()
    use_update = (all(os.path.exists(os.path.join(upd, n)) for n in REQUIRED)
                  and _version(upd) > _version(HERE))
    sys.path.insert(0, HERE)            # installed copy (also holds the bundled serial library)
    if use_update:
        sys.path.insert(0, upd)         # newer downloaded copy wins
    os.environ["CCR_START"] = os.path.abspath(__file__)
    if "--version" in sys.argv:  # diagnostics: which copy would run?
        import version
        print(f"{version.VERSION} from {os.path.dirname(os.path.abspath(version.__file__))}")
        return
    try:
        import car_code_reader
    except Exception:  # noqa: BLE001 - a broken update must never stop the app from opening
        if not use_update:
            raise
        sys.path.remove(upd)
        for name in list(sys.modules):
            if name in ("car_code_reader", "obd_core", "dtc_database", "icons", "vehicles", "version", "updater"):
                del sys.modules[name]
        import car_code_reader
    car_code_reader.main()


if __name__ == "__main__":
    main()
