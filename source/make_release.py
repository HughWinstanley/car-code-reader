#!/usr/bin/env python3
"""Build an update for the app's built-in updater.

    python make_release.py 2.3 "Short note about what changed" [out_dir]

Writes out_dir/release.json and out_dir/app/<files>; publish out_dir to the GitHub repo's main branch.
"""
import hashlib, json, os, shutil, sys

FILES = ["car_code_reader.py", "obd_core.py", "dtc_database.py", "icons.py", "vehicles.py", "updater.py", "j1939.py", "obd1.py", "maker_codes.py", "recalls.py", "service_guides.py",
         "icon.png"]

def main():
    version, notes = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else "release"
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(out, "app"), exist_ok=True)
    files = {}
    for name in FILES:
        with open(os.path.join(here, name), "rb") as f:
            data = f.read()
        files[name] = hashlib.sha256(data).hexdigest()
        with open(os.path.join(out, "app", name), "wb") as f:
            f.write(data)
    with open(os.path.join(out, "release.json"), "w") as f:
        json.dump({"version": version, "notes": notes, "files": files}, f, indent=2)
    print(f"Release {version}: {len(files)} files in {out}")

if __name__ == "__main__":
    main()
