#!/usr/bin/env python3
"""
Starts Car Code Reader. If a newer version has been downloaded by the in-app updater,
that copy is used; otherwise the installed copy is used.
This file itself is never replaced by updates.

It runs two ways:
- as a plain script next to the app's .py files (needs Python installed), or
- frozen inside the stand-alone Mac app (Python included). There the app's own .py files are kept
  as ordinary files in an "app" folder inside the bundle, NOT frozen, so updates can replace them.
"""

import os
import re
import sys

FROZEN = getattr(sys, "frozen", False)
if FROZEN:
    HERE = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)), "app")
    sys.dont_write_bytecode = True  # never write cache files inside the signed app bundle
else:
    HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ("car_code_reader.py", "obd_core.py", "dtc_database.py", "version.py")
APP_MODULES = ("car_code_reader", "obd_core", "dtc_database", "icons", "vehicles", "version", "updater",
               "j1939", "obd1")


def _bundle_hints():  # pragma: no cover - never called
    """Lists what the app's code uses, so the stand-alone build packs it in. (The app's own modules are
    left out of the frozen part on purpose, so the build can't see these imports by itself.)"""
    import csv, ctypes, datetime, hashlib, json, math, queue, shutil, socket, ssl, subprocess  # noqa
    import tempfile, threading, time, urllib.parse, urllib.request, webbrowser  # noqa
    import tkinter, tkinter.font, tkinter.ttk, tkinter.messagebox, tkinter.filedialog  # noqa
    import tkinter.scrolledtext  # noqa
    import serial, serial.tools.list_ports, serial.tools.list_ports_osx, serial.serialposix  # noqa


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


def _selftest():
    """Used by the build: prove the packed Python can load everything and start Tk."""
    import car_code_reader  # noqa: F401
    import j1939, obd1, serial.tools.list_ports  # noqa: F401
    import tkinter
    root = tkinter.Tcl()
    print("SELFTEST OK", car_code_reader.VERSION, "Tcl", root.eval("info patchlevel"),
          "from", os.path.dirname(car_code_reader.__file__))


def main():
    upd = _updates_dir()
    use_update = (all(os.path.exists(os.path.join(upd, n)) for n in REQUIRED)
                  and _version(upd) > _version(HERE))
    sys.path.insert(0, HERE)            # installed copy (also holds the bundled serial library)
    if use_update:
        sys.path.insert(0, upd)         # newer downloaded copy wins
    os.environ["CCR_START"] = os.path.abspath(__file__) if not FROZEN else sys.executable
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
            if name in APP_MODULES:
                del sys.modules[name]
        import car_code_reader
    if "--selftest" in sys.argv:
        _selftest()
        return
    car_code_reader.main()


if __name__ == "__main__":
    main()
